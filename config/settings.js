const BRANCH_COORDINATES = {
  Kondapur: [17.4354, 78.3775],
  Madhapur: [17.4409, 78.3490],
  Manikonda: [17.4578, 78.3701],
  Nizampet: [17.5152, 78.3385],
  Nanakramguda: [17.4632, 78.3813],
  'West Maredpally': [17.4558529177458, 78.50727064061495]
};

const DELIVERY_RADIUS_KM = 6.0;

const ORDER_STATUS = {
  PENDING: 'Pending',
  PAID: 'Paid',
  READY: 'Ready',
  ON_THE_WAY: 'On The Way',
  DELIVERED: 'Delivered',
  CANCELLED: 'Cancelled'
};

const PRODUCT_CATALOG = {};

function setBrandCatalog(brandConfig) {
  for (const key of Object.keys(PRODUCT_CATALOG)) {
    delete PRODUCT_CATALOG[key];
  }
  for (const item of brandConfig.catalog || []) {
    // Store catalog entries using lowercase ids to allow case-insensitive lookups
    const key = String(item.id).toLowerCase();
    PRODUCT_CATALOG[key] = { name: item.name, price: item.price };
  }
}

const BRANCH_CONTACTS = {
  Kondapur: ['916302588275'],
  Madhapur: ['917075442898'],
  Manikonda: ['919392016847'],
  Nizampet: ['916303241076'],
  Nanakramguda: ['916303237242'],
  'West Maredpally': ['919032366276']
};

const OTHER_NUMBERS = ['9640112005', '9226454238', '8074301029'];

module.exports = {
  BRANCH_COORDINATES,
  DELIVERY_RADIUS_KM,
  ORDER_STATUS,
  PRODUCT_CATALOG,
  setBrandCatalog,
  BRANCH_CONTACTS,
  OTHER_NUMBERS
};
