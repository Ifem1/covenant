import {z} from 'zod';
export const Source=z.string().url().refine(u=>{const x=new URL(u);return x.protocol==='https:'&&!x.username&&!x.password&&!/^(localhost|127\.|10\.|192\.168\.)/.test(x.hostname)},'HTTPS public URL required');
export const Clause=z.object({id:z.number().int().positive(),label:z.string().max(80),criterion:z.string().max(500),slashBps:z.number().int().min(0).max(10000),minimumSources:z.number().int().min(1).max(5)});
export const Finding=z.object({clauseId:z.number(),finding:z.enum(['COMPLIED','BREACHED','INCONCLUSIVE','UNAVAILABLE']),severity:z.enum(['LOW','MEDIUM','HIGH']),evidence:z.array(z.object({sourceId:z.number(),excerpt:z.string().max(300)})).max(5),observedEventDate:z.string().max(20),reason:z.string().max(240)});
