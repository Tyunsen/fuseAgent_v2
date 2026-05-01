import { FlatCompat } from '@eslint/eslintrc';
import { dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
});

const eslintConfig = [
  {
    ignores: [
      'src/api/**/*',
      'build/**/*',
      '.next/**/*',
      'node_modules/**/*',
      'coverage/**/*',
    ],
  },
  ...compat.extends('next/core-web-vitals', 'next/typescript'),
  ...compat.config({
    extends: ['next', 'prettier'],
    rules: {
      '@typescript-eslint/no-explicit-any': 'warn',
      '@next/next/no-img-element': 'off',
    },
  }),
];

export default eslintConfig;
