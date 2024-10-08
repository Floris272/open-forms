const path = require('path');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');

const config = {
  core: {
    disableTelemetry: true,
    disableWhatsNewNotifications: true,
  },
  stories: ['../src/openforms/js/**/*.mdx', '../src/openforms/js/**/*.stories.@(js|jsx|ts|tsx)'],

  staticDirs: [
    {from: '../static/admin', to: 'static/admin'},
    {from: '../static/fonts', to: 'static/fonts'},
    {from: '../static/img', to: 'static/img'},
    // required in dev mode due to style-loader usage
    {from: '../static/admin', to: 'admin'},
    {from: '../static/fonts', to: 'fonts'},
    {from: '../static/img', to: 'img'},
    {from: '../public', to: ''},
  ],

  addons: [
    '@storybook/addon-links',
    '@storybook/addon-essentials',
    '@storybook/addon-interactions',
    'storybook-react-intl',
    '@storybook/addon-webpack5-compiler-babel',
  ],
  features: {
    interactionsDebugger: true,
    buildStoriesJson: true,
  },

  framework: {
    name: '@storybook/react-webpack5',
    options: {},
  },

  env: config => ({
    ...config,
    API_BASE_URL: process.env.API_BASE_URL || '',
  }),

  webpackFinal: async (config, {configType}) => {
    const isEnvProduction = configType === 'PRODUCTION';

    config.resolve.modules = [
      ...(config.resolve.modules || []),
      'node_modules',
      path.resolve(__dirname, '../src/openforms/js'),
    ];

    if (isEnvProduction) {
      config.plugins.push(new MiniCssExtractPlugin({filename: 'static/bundles/[name].css'}));
    }

    config.module.rules.push(
      // .scss
      {
        test: /\.scss$/,
        use: [
          !isEnvProduction && {loader: 'style-loader'},
          // Writes css files.
          isEnvProduction && MiniCssExtractPlugin.loader,
          // Loads CSS files.
          {
            loader: 'css-loader',
            options: {
              url: false,
            },
          },
          // Runs postcss configuration (postcss.config.js).
          {loader: 'postcss-loader'},
          // Compiles .scss to .css.
          {
            loader: 'sass-loader',
            options: {
              sassOptions: {
                comments: false,
                style: 'compressed',
              },
              // sourceMap: argv.sourcemap,
            },
          },
        ].filter(Boolean),
      }
    );
    return config;
  },

  docs: {},
};

export default config;
