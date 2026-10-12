import {
  type FeishuTableManifest,
  FeishuTableProvider,
} from '@aeolus/feishu-table-sdk';
import { type PropsWithChildren, useState } from 'react';
import manifest from '../../web-application.json';

export function DataApplicationProvider({ children }: PropsWithChildren) {
  const [dataManifest] = useState<FeishuTableManifest>(() => {
    if (typeof window !== 'undefined') {
      window.webApplicationManifest = manifest as FeishuTableManifest;
      window.__AEOLUS_FEISHU_SEND_BINDING__ = true;
    }
    return manifest as FeishuTableManifest;
  });

  return (
    <FeishuTableProvider manifest={dataManifest}>
      {children}
    </FeishuTableProvider>
  );
}
