import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createClient, createAccount} from 'genlayer-js';
import {CalldataAddress} from 'genlayer-js/types';
import {hexToBytes} from 'viem';
import {studionet} from 'genlayer-js/chains';

const rpc = process.env.GLSIM_RPC_URL ?? 'http://127.0.0.1:4000/api';
const key = process.env.GLSIM_TEST_PRIVATE_KEY ?? '0x0123456789012345678901234567890123456789012345678901234567890123';
const account = createAccount(key);
const client = createClient({chain: {...studionet, rpcUrls: {default: {http: [rpc]}}}, account});
const code = file => fs.readFileSync(file, 'utf8');
const addr = `0x${'11'.repeat(20)}`;
const other = createAccount('0xabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcd');
const ca = value => new CalldataAddress(hexToBytes(value));

async function finalized(hash) {
  const receipt = await client.waitForTransactionReceipt({hash, interval: 100, retries: 100});
  const execution = String(receipt.txExecutionResultName ?? receipt.executionResult ?? '').toUpperCase();
  assert(['SUCCESS', 'SUCCESSFUL', 'SUCCEEDED'].includes(execution), `GenLayer execution was not successful: ${JSON.stringify(receipt)}`);
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

const registry = await deploy('contracts/covenant_registry.py', [ca(account.address)]);
assert.equal(String(await client.readContract({address: registry, functionName: 'get_canonical_vault'})), '0x0000000000000000000000000000000000000000');
const vault = await deploy('contracts/covenant_vault.py', [ca(registry)]);
await write(registry, 'bind_canonical_vault', [ca(vault)]);
assert.equal(String(await client.readContract({address: registry, functionName: 'get_canonical_vault'})).toLowerCase(), vault.toLowerCase());
await expectFailure(() => write(registry, 'bind_canonical_vault', [ca(addr)]));

const clauses = [{clause_id: 1, text: 'availability', slash_bps: 2500, minimum_sources: 1}];
const sources = [{source_id: 1, url: 'https://example.com/a'}, {source_id: 2, url: 'https://example.com/b'}];
const recovery = `0x${'22'.repeat(20)}`;
const createArgs = (overrides = {}) => ['service', 'description', recovery, 100n, 10n, 20n, clauses, sources].map((v, i) => overrides[i] ?? v);
const create = await client.writeContract({address: registry, functionName: 'create_covenant', args: createArgs({2: ca(recovery)}), account, value: 0n});
const createReceipt = await finalized(create);
assert(createReceipt);
const covenant = await client.readContract({address: registry, functionName: 'get_covenant', args: [0n]});
assert.equal(covenant.service, 'service'); assert.equal(covenant.description, 'description');
assert.equal(covenant.clauses[0].text, 'availability'); assert.equal(covenant.sources[1].url, sources[1].url);
await expectFailure(() => client.writeContract({address: registry, functionName: 'mark_funded', args: [0n], account: other, value: 0n}).then(finalized));
await expectFailure(() => client.writeContract({address: registry, functionName: 'bind_canonical_vault', args: [ca(addr)], account: other, value: 0n}).then(finalized));
await expectFailure(() => write(registry, 'bind_canonical_vault', [ca(addr)]));
await expectFailure(() => client.writeContract({address: registry, functionName: 'create_covenant', args: createArgs({3: 0n}), account, value: 0n}).then(finalized));
await expectFailure(() => client.writeContract({address: registry, functionName: 'create_covenant', args: createArgs({2: ca(account.address)}), account, value: 0n}).then(finalized));
await expectFailure(() => client.writeContract({address: registry, functionName: 'create_covenant', args: createArgs({7: [{source_id: 1, url: 'http://example.com/a'}, sources[1]]}), account, value: 0n}).then(finalized));
await expectFailure(() => client.writeContract({address: registry, functionName: 'create_covenant', args: createArgs({7: [sources[0], {source_id: 2, url: sources[0].url}]}), account, value: 0n}).then(finalized));
await expectFailure(() => client.writeContract({address: registry, functionName: 'create_covenant', args: createArgs({6: [{clause_id: 1, text: 'a', slash_bps: 1, minimum_sources: 1}, {clause_id: 1, text: 'b', slash_bps: 1, minimum_sources: 1}]}), account, value: 0n}).then(finalized));
console.log(JSON.stringify({runtime: 'glsim', rpc, chainId: 61999, tests: 14, passed: 14, failed: 0, skipped: 0, registry, vault}, null, 2));
