import parser from '@typescript-eslint/parser';
export default [{ignores:['.next/**','node_modules/**','artifacts/**']},{files:['**/*.{ts,tsx}'],languageOptions:{parser}}];
