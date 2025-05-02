const path = require('path');
const Dotenv = require('dotenv-webpack');

module.exports = {
  entry: './src/app.ts',
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: 'ts-loader',
        exclude: /node_modules/,
      },
    ],
  },
  resolve: {
    extensions: ['.tsx', '.ts', '.js'],
  },
  output: {
    filename: 'app.bundle.js',
    path: path.resolve(__dirname, 'dist'),
  },
  plugins: [
    new Dotenv({
      systemvars: true, // Load all system variables
    }),
  ],
  // Ensure ES5 compatibility for older browsers like Safari
  target: ['web', 'es5'],
};