import {createPublicClient,createWalletClient,custom,http,type EIP1193Provider} from 'viem';
import {STUDIONET} from '../network';
export const studionetChain={id:STUDIONET.chainId,name:STUDIONET.name,nativeCurrency:{name:'GEN',symbol:'GEN',decimals:18},rpcUrls:{default:{http:[STUDIONET.rpc]}}} as const;
export const publicClient=createPublicClient({chain:studionetChain,transport:http(STUDIONET.rpc)});
export function walletClient(provider:EIP1193Provider){return createWalletClient({chain:studionetChain,transport:custom(provider)})}
export type TxPhase='AWAITING_SIGNATURE'|'SUBMITTED'|'FINALIZED'|'EXECUTION_CONFIRMED'|'FAILED';
