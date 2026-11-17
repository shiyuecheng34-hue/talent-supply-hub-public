import { industryAvatarSprites } from '@/data/industryAvatarSprites';
import { useEffect, useState } from 'react';
import { AgencyAvatar } from './AgencyAvatar';

type Sprite = {
  avatarUrl: string;
  avatarPosition: string;
  spriteSize: [number, number];
};

// P0 头像图集 3MB+，按需加载一次后在所有行间共享，避免压进首屏主包。
let cache: Record<string, Sprite> | null = null;
let pending: Promise<void> | null = null;

function useSpriteMap() {
  const [map, setMap] = useState<Record<string, Sprite> | null>(cache);
  useEffect(() => {
    if (cache) return;
    pending ??= import('@/data/p0AvatarSprites').then(module => {
      cache = module.p0AvatarSprites as Record<string, Sprite>;
    });
    let cancelled = false;
    pending
      .then(() => {
        if (!cancelled) setMap(cache);
      })
      .catch(() => {
        // 图集加载失败时回退到代理商头像与姓名兜底，不影响表格。
      });
    return () => {
      cancelled = true;
    };
  }, []);
  return map;
}

export function P0Avatar({ id, name }: { id: string; name: string }) {
  const sprites = useSpriteMap();
  // P0 专属图集 → 行业图集（已在主包）→ 代理商头像组件（代理图集/兜底）。
  const sprite = sprites?.[id] ?? industryAvatarSprites[id];
  if (!sprite) return <AgencyAvatar id={id} name={name} />;
  return (
    <span className="avatar avatar-photo" title={`${name} 头像`}>
      <span
        className="avatar-sprite"
        style={{
          backgroundImage: `url(${sprite.avatarUrl})`,
          backgroundPosition: sprite.avatarPosition,
          backgroundSize: `${sprite.spriteSize[0]}px ${sprite.spriteSize[1]}px`,
        }}
        role="img"
        aria-label={`${name} 头像`}
      />
    </span>
  );
}
