import {createPublicClient,createWalletClient,custom,http,type EIP1193Provider} from 'viem';
import {STUDIONET} from '../network';
export const studionetChain={id:STUDIONET.chainId,name:STUDIONET.name,nativeCurrency:{name:'GEN',symbol:'GEN',decimals:18},rpcUrls:{default:{http:[STUDIONET.rpc]}}} as const;
export const publicClient=createPublicClient({chain:studionetChain,transport:http(STUDIONET.rpc)});
export function walletClient(provider:EIP1193Provider){return createWalletClient({chain:studionetChain,transport:custom(provider)})}
export async function ensureStudionet(provider:EIP1193Provider){const p=provider as EIP1193Provider & {request:(a:{method:string;params?:unknown[]})=>Promise<unknown>};if(Number(await p.request({method:'eth_chainId'}))===STUDIONET.chainId)return;try{await p.request({method:'wallet_switchEthereumChain',params:[{chainId:`0x${STUDIONET.chainId.toString(16)}`}]})}catch{await p.request({method:'wallet_addEthereumChain',params:[{chainId:`0x${STUDIONET.chainId.toString(16)}`,chainName:STUDIONET.name,nativeCurrency:{name:'GEN',symbol:'GEN',decimals:18},rpcUrls:[STUDIONET.rpc],blockExplorerUrls:[STUDIONET.explorer]}]})}}
export type TxPhase='AWAITING_SIGNATURE'|'SUBMITTED'|'FINALIZED'|'EXECUTION_CONFIRMED'|'FAILED';
