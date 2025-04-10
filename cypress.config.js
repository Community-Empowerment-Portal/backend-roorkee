const { defineConfig } = require('cypress')
const webpackPreprocessor = require('@cypress/webpack-preprocessor')
const path = require('path')

module.exports = defineConfig({
  e2e: {
    baseUrl: 'http://127.0.0.1:8000/admin',
    setupNodeEvents(on, config) {
      // Configure webpack preprocessor with enhanced module resolution
      const options = {
        webpackOptions: {
          resolve: {
            extensions: ['.js', '.jsx', '.json'],
            alias: {
              '@cypress': path.resolve(__dirname, 'cypress'),
              '@helpers': path.resolve(__dirname, 'cypress/support/helpers'),
              '@fixtures': path.resolve(__dirname, 'cypress/fixtures'),
              '@utils': path.resolve(__dirname, 'cypress/support/utils')
            }
          },
          module: {
            rules: [
              {
                test: /\.js$/,
                exclude: /node_modules/,
                use: {
                  loader: 'babel-loader',
                  options: {
                    presets: ['@babel/preset-env']
                  }
                }
              }
            ]
          }
        }
      }
      on('file:preprocessor', webpackPreprocessor(options))
      
      return config
    },
    experimentalSessionAndOrigin: true,
    defaultCommandTimeout: 10000,
    pageLoadTimeout: 30000,
    viewportWidth: 1200,
    viewportHeight: 800,
    env: {
      admin_username: 'admin',
      admin_password: 'adminpassword'
    },
    retries: {
      runMode: 2,
      openMode: 0
    },
    screenshotOnRunFailure: true,
    video: false,
    chromeWebSecurity: false
  }
})
