function getCurrentIST() {
  return new Date(new Date().toLocaleString('en-US', { timeZone: 'Asia/Kolkata' }));
}

function getISTISOTime() {
  return getCurrentIST().toISOString();
}

module.exports = { getCurrentIST, getISTISOTime };
