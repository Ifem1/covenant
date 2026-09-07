import type {Metadata} from 'next'; import './globals.css'; import WalletButton from '@/components/WalletButton';
export const metadata:Metadata={title:'Covenant — bonded operational promises',description:'Public promises. Bonded consequences. No private monitor.'};
export default function Layout({children}:{children:React.ReactNode}){return <html lang="en"><body>{children}<WalletButton/></body></html>}
