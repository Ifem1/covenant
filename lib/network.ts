export const STUDIONET={name:'GenLayer Studionet',chainId:61999,rpc:'https://studio.genlayer.com/api',explorer:'https://explorer-studio.genlayer.com',currency:'GEN'} as const;
export function assertStudionet(chainId:number){if(chainId!==STUDIONET.chainId)throw new Error(`Wrong network: expected ${STUDIONET.chainId}`)}
