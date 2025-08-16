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

const PRODUCT_CATALOG = {
  '6xpxtkaoau': { name: 'Palm Jaggery - Powdered(700gms)', price: 760 },
  'kyygkhdlxf': { name: 'Palm Jaggery - cubes(1 KG)', price: 1100 },
  '1ado92c3xm': { name: 'Palm Jaggery - Powdered(1 KG)', price: 1100 },
  '36dlxrjdjq': { name: 'Palm Jaggery - Powdered(500gms)', price: 550 },
  hkaqqb8sec: { name: 'Palm Jaggery - cubes(500gms)', price: 550 }
};

module.exports = { BRANCH_COORDINATES, DELIVERY_RADIUS_KM, ORDER_STATUS, PRODUCT_CATALOG };
