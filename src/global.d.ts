import type { FeishuTableManifest } from '@aeolus/feishu-table-sdk';

declare global {
  interface Window {
    webApplicationManifest?: FeishuTableManifest;
    __AEOLUS_FEISHU_SEND_BINDING__?: boolean;
  }
}
