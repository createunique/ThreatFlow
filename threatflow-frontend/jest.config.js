module.exports = {
  preset: 'react-scripts',
  transformIgnorePatterns: [
    'node_modules/(?!axios)',
  ],
  moduleNameMapper: {
    '^axios$': 'axios/dist/node/axios.cjs',
  },
};