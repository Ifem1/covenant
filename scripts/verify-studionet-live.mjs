import assert from 'node:assert/strict';
import {createClient, createAccount} from 'genlayer-js';
import {CalldataAddress} from 'genlayer-js/types';
import {hexToBytes} from 'viem';
import {studionet} from 'genlayer-js/chains';

const key=process.env.COVENANT_DEPLOYER_PRIVATE_KEY;
if(!key) throw new Error('Set COVENANT_DEPLOYER_PRIVATE_KEY');
const registry=process.env.COVENANT_REGISTRY_ADDRESS;
const vault=process.env.COVENANT_VAULT_ADDRESS;
if(!registry||!vault) throw new Error('Set COVENANT_REGISTRY_ADDRESS and COVENANT_VAULT_ADDRESS');
const account=createAccount(key); const client=createClient({chain:studionet,account});
const ca=value=>new CalldataAddress(hexToBytes(value));
async function finalized(hash){const r=await client.waitForTransactionReceipt({hash,interval:100,retries:300});const e=String(r.txExecutionResultName??r.executionResult??'').toUpperCase();const leader=r.consensus_data?.leader_receipt?.[0]?.execution_result;const accepted=String(r.status_name??'').toUpperCase()==='ACCEPTED';assert(accepted&&(['SUCCESS','SUCCESSFUL','SUCCEEDED'].includes(e)||String(r.result)==='6'||leader==='SUCCESS'),JSON.stringify({hash,status:r.status_name,result:r.result,execution:e,leader}));return r;}
async function write(address,functionName,args=[],value=0n){return finalized(await client.writeContract({address,functionName,args,account,value}));}
const clauses=[{clause_id:1,text:'availability',slash_bps:2500,minimum_sources:1}];
const sources=[{source_id:1,url:'https://example.com/a'},{source_id:2,url:'https://example.com/b'}];
const recovery='0x2222222222222222222222222222222222222222';
const cid=0n;
let c=await client.readContract({address:registry,functionName:'get_covenant',args:[cid]});
assert.equal(c.service,'service');
if(c.status==='DRAFT') { const existingBond=await client.readContract({address:vault,functionName:'get_bond',args:[cid]}); assert(BigInt(existingBond)===0n,`Refusing to deposit over existing bond: ${existingBond}`); await write(vault,'deposit_bond',[cid],100n); const afterDeposit=await client.readContract({address:registry,functionName:'get_covenant',args:[cid]}); if(afterDeposit.status==='DRAFT') await write(vault,'reconcile_funding',[cid]); }
const funded=await client.readContract({address:registry,functionName:'get_covenant',args:[cid]}); if(!['FUNDED','ACTIVE'].includes(funded.status)) throw new Error(`Existing covenant is not lifecycle-ready: ${JSON.stringify(funded)}`);
if(funded.status==='FUNDED') await write(registry,'activate',[cid]);
const active=await client.readContract({address:registry,functionName:'get_covenant',args:[0n]}); assert.equal(active.status,'ACTIVE');
console.log(JSON.stringify({chainId:61999,admin:account.address,registry,vault,covenantId:'0',funded:funded.status,active:active.status,bond:await client.readContract({address:vault,functionName:'get_bond',args:[0n]})},null,2));
