// @ts-check

const repository = process.env.GITHUB_REPOSITORY || 'liyujie43/arkui-specs';
const [repositoryOwner, repositoryName] = repository.split('/');
const siteUrl = process.env.SITE_URL || `https://${repositoryOwner}.github.io`;
const baseUrl = process.env.BASE_URL || `/${repositoryName}/`;
const repositoryUrl = `https://github.com/${repository}`;

const config = {
  title: 'ArkUI Specs',
  tagline: 'Registry-driven ArkUI feature specifications',

  url: siteUrl,
  baseUrl,

  organizationName: repositoryOwner,
  projectName: repositoryName,
  deploymentBranch: 'gh-pages',
  trailingSlash: false,
  onBrokenLinks: 'warn',
  markdown: {
    format: 'detect',
    mermaid: true,
    hooks: {
      onBrokenMarkdownLinks: 'warn',
    },
  },
  themes: ['@docusaurus/theme-mermaid'],

  i18n: {
    defaultLocale: 'zh-CN',
    locales: ['zh-CN'],
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          path: 'docs',
          routeBasePath: 'docs',
          sidebarPath: require.resolve('./sidebars.js'),
          numberPrefixParser: false,
          showLastUpdateTime: false,
        },
        blog: false,
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      navbar: {
        title: 'ArkUI Specs',
        items: [
          { to: '/', label: 'Portal', position: 'left' },
          { to: '/docs', label: 'Docs', position: 'left' },
          {
            href: repositoryUrl,
            label: 'GitHub',
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Docs',
            items: [
              { label: 'Index', to: '/docs' },
              { label: 'Registry', to: '/docs/registry' },
            ],
          },
          {
            title: 'Source',
            items: [
              { label: 'GitHub', href: repositoryUrl },
            ],
          },
        ],
        copyright: `Copyright (c) ${new Date().getFullYear()} ArkUI Specs contributors.`,
      },
      prism: {
        additionalLanguages: ['bash', 'cpp', 'typescript', 'yaml'],
      },
      tableOfContents: {
        minHeadingLevel: 2,
        maxHeadingLevel: 4,
      },
    }),
};

module.exports = config;
