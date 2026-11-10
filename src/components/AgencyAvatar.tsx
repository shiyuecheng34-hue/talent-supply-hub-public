import { douyinAvatarMap } from '@/data/douyinAvatarMap';
import { useState } from 'react';

export function AgencyAvatar({ id, name }: { id: string; name: string }) {
  const avatar = douyinAvatarMap[id];
  const [failed, setFailed] = useState(false);
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
            backgroundSize: '2240px 1792px',
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
