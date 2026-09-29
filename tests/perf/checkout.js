import { check, fail, sleep } from 'k6';
import http from 'k6/http';
import { Trend } from 'k6/metrics';
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.1.0/index.js';
import { htmlReport } from 'https://raw.githubusercontent.com/benc-uk/k6-reporter/main/dist/bundle.js';

// Stateful write path: register -> login -> add to basket -> checkout.
// Read-only product listing would prove nothing interesting about the SUT.

const BASE_URL = __ENV.BASE_URL;
const PASSWORD = __ENV.TEST_USER_PASSWORD;

if (!BASE_URL || !PASSWORD) {
  throw new Error('BASE_URL and TEST_USER_PASSWORD must be set (see .env.example).');
}

const checkoutDuration = new Trend('checkout_duration', true);

// This profile places ~190 orders across ~43 eligible SKUs (~5 each). 20 units
// of headroom keeps stock from running out mid-run and skewing the results.
const MIN_STOCK = 20;

export const options = {
  scenarios: {
    checkout_load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: 10 },
        { duration: '1m', target: 10 },
        { duration: '30s', target: 0 },
      ],
      gracefulRampDown: '15s',
    },
  },
  // Pass/fail gates. A perf test that cannot fail is not a test.
  //
  // Calibrated from a local baseline against the Dockerized SUT at this load:
  // http_req_duration p95 ~42ms, checkout_duration p95 ~50ms. The gates sit at
  // roughly 5x that — loose enough to absorb a slower CI runner, tight enough
  // that a real regression trips them. Recalibrate from CI's first green run.
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<250'],
    checkout_duration: ['p(95)<300'],
    checks: ['rate>0.99'],
  },
};

const JSON_HEADERS = { 'Content-Type': 'application/json' };

// `name` groups metrics: pass a static one for paths containing ids, otherwise
// every VU's basket id becomes its own metric series.
function post(path, body, token, name = path) {
  const headers = token ? { ...JSON_HEADERS, Authorization: `Bearer ${token}` } : JSON_HEADERS;
  return http.post(`${BASE_URL}${path}`, JSON.stringify(body), { headers, tags: { name } });
}

/**
 * Juice Shop stocks a finite quantity per product, so the load has to be spread
 * across the catalogue — hammering one SKU drains it and turns every later
 * iteration into a 400, measuring the error path instead of checkout.
 */
export function setup() {
  const catalogue = http.get(`${BASE_URL}/rest/products/search?q=`);
  if (catalogue.status !== 200) {
    fail(`could not load the product catalogue: ${catalogue.status}`);
  }
  const stock = http.get(`${BASE_URL}/api/Quantitys`);
  if (stock.status !== 200) {
    fail(`could not load product stock levels: ${stock.status}`);
  }

  // A fresh Juice Shop seeds some products at quantity 0 and others in the
  // single digits. Both drain during a run and turn checkout into a 400, so
  // the load only targets SKUs deep enough to absorb this run's order volume.
  const inStock = new Set(
    stock
      .json('data')
      .filter((q) => q.quantity >= MIN_STOCK)
      .map((q) => q.ProductId),
  );
  const productIds = catalogue
    .json('data')
    .map((p) => p.id)
    .filter((id) => inStock.has(id));

  if (productIds.length === 0) {
    fail('no products are in stock — the SUT needs a reset');
  }
  return { productIds };
}

export default function (data) {
  const { productIds } = data;
  // Deterministic spread so concurrent VUs contend for different SKUs.
  const productId = productIds[(__VU * 31 + __ITER) % productIds.length];
  const email = `perf.${__VU}.${__ITER}.${Date.now()}@e2e.test`;

  const registered = post('/api/Users/', {
    email,
    password: PASSWORD,
    passwordRepeat: PASSWORD,
    securityQuestion: { id: 1 },
    securityAnswer: 'perf',
  });
  if (!check(registered, { registered: (r) => r.status === 201 })) {
    fail(`registration failed: ${registered.status} ${registered.body}`);
  }

  const loggedIn = post('/rest/user/login', { email, password: PASSWORD });
  if (!check(loggedIn, { 'logged in': (r) => r.status === 200 })) {
    fail(`login failed: ${loggedIn.status} ${loggedIn.body}`);
  }
  const { token, bid } = loggedIn.json('authentication');

  // Think time: a real customer browses before adding to the basket. Without
  // it the VUs generate an unrealistic order rate and exhaust the catalogue.
  sleep(2);

  const added = post('/api/BasketItems/', { BasketId: bid, ProductId: productId, quantity: 1 }, token);
  if (!check(added, { 'added to basket': (r) => r.status === 200 })) {
    fail(`add to basket failed: ${added.status} ${added.body}`);
  }

  sleep(2);

  const address = post(
    '/api/Addresss/',
    {
      fullName: 'Perf User',
      mobileNum: 1234567890,
      zipCode: '12345',
      streetAddress: '1 Test Street',
      city: 'Testville',
      state: 'TS',
      country: 'Testland',
    },
    token,
  );
  const card = post(
    '/api/Cards/',
    { fullName: 'Perf User', cardNum: '4111111111111111', expMonth: 12, expYear: 2080 },
    token,
  );
  check(address, { 'address created': (r) => r.status === 201 });
  check(card, { 'card created': (r) => r.status === 201 });

  sleep(1);

  const checkout = post(
    `/rest/basket/${bid}/checkout`,
    {
      couponData: '',
      orderDetails: {
        addressId: address.json('data.id'),
        paymentId: card.json('data.id'),
        deliveryMethodId: 3,
      },
    },
    token,
    '/rest/basket/{bid}/checkout',
  );
  checkoutDuration.add(checkout.timings.duration);
  check(checkout, {
    'order confirmed': (r) => r.status === 200 && !!r.json('orderConfirmation'),
  });
}

// Defining handleSummary() replaces k6's default outputs entirely, so the
// JSON export (still consumed by CI as the archived artifact) and stdout text
// have to be produced here alongside the HTML report.
export function handleSummary(data) {
  return {
    'perf-summary.json': JSON.stringify(data),
    'perf-summary.html': htmlReport(data),
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
  };
}
