import type {Metadata} from 'next'; import './globals.css';
export const metadata:Metadata={title:'Covenant — bonded operational promises',description:'Public promises. Bonded consequences. No private monitor.'};
export default function Layout({children}:{children:React.ReactNode}){return <html lang="en"><body>{children}</body></html>}
