import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createClient, createAccount} from 'genlayer-js';
import {studionet} from 'genlayer-js/chains';

const rpc = process.env.GLSIM_RPC_URL ?? 'http://127.0.0.1:4000/api';
const key = process.env.GLSIM_TEST_PRIVATE_KEY ?? '0x0123456789012345678901234567890123456789012345678901234567890123';
const account = createAccount(key);
const client = createClient({chain: {...studionet, rpcUrls: {default: {http: [rpc]}}}, account});
const code = file => fs.readFileSync(file, 'utf8');
const addr = `0x${'11'.repeat(20)}`;
const other = createAccount('0xabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcd');

async function finalized(hash) {
  const receipt = await client.waitForTransactionReceipt({hash, interval: 100, retries: 100});
  const execution = receipt.txExecutionResultName ?? receipt.executionResult ?? receipt.result;
  assert(!['ERROR', 'FAILED', 'REJECTED', '0'].includes(String(execution).toUpperCase()), `GenLayer execution failed: ${JSON.stringify(receipt)}`);
  return receipt;
}
async function write(address, functionName, args = [], signer = client) {
  const hash = await signer.writeContract({address, functionName, args, account: signer.account, value: 0n});
  return finalized(hash);
}
async function expectFailure(fn) { await assert.rejects(fn); }
async function deploy(file, args) {
  const hash = await client.deployContract({code: code(file), args, account});
  const receipt = await finalized(hash);
  const address = receipt.contractAddress ?? receipt.txDataDecoded?.contractAddress ?? receipt.data?.contract_address;
  assert(address, `No deployed address: ${JSON.stringify(receipt)}`);
  return address;
}

const registry = await deploy('contracts/covenant_registry.py', [account.address]);
assert.equal(String(await client.readContract({address: registry, functionName: 'get_canonical_vault'})), '0x0000000000000000000000000000000000000000');
const vault = await deploy('contracts/covenant_vault.py', [registry]);
await write(registry, 'bind_canonical_vault', [vault]);
assert.equal(String(await client.readContract({address: registry, functionName: 'get_canonical_vault'})).toLowerCase(), vault.toLowerCase());
await expectFailure(() => write(registry, 'bind_canonical_vault', [addr]));

const clauses = [{clause_id: 1, text: 'availability', slash_bps: 2500, minimum_sources: 1}];
const sources = [{source_id: 1, url: 'https://example.com/a'}, {source_id: 2, url: 'https://example.com/b'}];
const recovery = `0x${'22'.repeat(20)}`;
const create = await client.writeContract({address: registry, functionName: 'create_covenant', args: ['service', 'description', recovery, 100n, 10n, 20n, clauses, sources], account, value: 0n});
const createReceipt = await finalized(create);
assert(createReceipt);
const covenant = await client.readContract({address: registry, functionName: 'get_covenant', args: [0n]});
assert.equal(covenant.service, 'service'); assert.equal(covenant.description, 'description');
assert.equal(covenant.clauses[0].text, 'availability'); assert.equal(covenant.sources[1].url, sources[1].url);
await expectFailure(() => client.writeContract({address: registry, functionName: 'mark_funded', args: [0n], account: other, value: 0n}).then(finalized));
console.log(JSON.stringify({runtime: 'glsim', rpc, chainId: 61999, tests: 8, passed: 8, failed: 0, registry, vault}, null, 2));
