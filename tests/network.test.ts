import {describe,it,expect} from 'vitest'; import {STUDIONET,assertStudionet} from '../lib/network';
describe('canonical network',()=>{it('locks production target',()=>{expect(STUDIONET.chainId).toBe(61999);expect(STUDIONET.rpc).toBe('https://studio.genlayer.com/api')});it('rejects drift',()=>expect(()=>assertStudionet(61997)).toThrow())});
