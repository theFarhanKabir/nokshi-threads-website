import { siteContent } from './site-content';
import { ChatWidget } from './chat-widget';

export default function Home() {
  return (
    <>
      <div dangerouslySetInnerHTML={{ __html: siteContent }} />
      <ChatWidget />
    </>
  );
}
