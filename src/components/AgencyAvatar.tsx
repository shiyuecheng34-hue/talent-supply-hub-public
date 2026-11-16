import { agencyAvatarSprites } from '@/data/agencyAvatarSprites';
import { douyinAvatarMap, douyinAvatarMeta } from '@/data/douyinAvatarMap';
import { useState } from 'react';

export function AgencyAvatar({ id, name }: { id: string; name: string }) {
  const avatar = agencyAvatarSprites[id] ?? douyinAvatarMap[id];
  const [failed, setFailed] = useState(false);
  const spriteSize = agencyAvatarSprites[id]?.spriteSize ??
    douyinAvatarMeta.spriteSize ?? [4000, 3200];
  const fallback = Array.from(name || '达人')
    .slice(0, 2)
    .join('');
  return (
    <span
      className="avatar avatar-photo"
      title={avatar && !failed ? `${name} 头像` : `${name}：暂无头像，姓名兜底`}
    >
      {!failed && avatar?.avatarPosition ? (
        <span
          className="avatar-sprite"
          style={{
            backgroundImage: `url(${avatar.avatarUrl})`,
            backgroundPosition: avatar.avatarPosition,
            backgroundSize: `${spriteSize[0]}px ${spriteSize[1]}px`,
          }}
          role="img"
          aria-label={`${name} 头像`}
        />
      ) : !failed && avatar?.avatarUrl ? (
        <img
          src={avatar.avatarUrl}
          alt={`${name} 头像`}
          onError={() => setFailed(true)}
        />
      ) : (
        <span>{fallback}</span>
      )}
    </span>
  );
}
