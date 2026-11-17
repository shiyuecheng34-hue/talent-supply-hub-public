export type IndustryOption = {
  id: string;
  label: string;
  sheetId: string;
  count: number;
  color: string;
};

export const INDUSTRY_OPTIONS: IndustryOption[] = [
  {
    id: 'industry-beauty',
    label: '美妆',
    sheetId: '0OYgsp',
    count: 7389,
    color: '#ff7eb6',
  },
  {
    id: 'industry-food',
    label: '食品饮料',
    sheetId: '1RZNHB',
    count: 1969,
    color: '#ffad66',
  },
  {
    id: 'industry-fashion',
    label: '服装配饰',
    sheetId: '2JBIVb',
    count: 2761,
    color: '#ffd166',
  },
  {
    id: 'industry-mom',
    label: '母婴宠物',
    sheetId: '3UBBZb',
    count: 1733,
    color: '#7ee081',
  },
  {
    id: 'industry-care',
    label: '日化',
    sheetId: '4QiWFQ',
    count: 5728,
    color: '#2dd4a7',
  },
  {
    id: 'industry-health',
    label: '医药健康',
    sheetId: '5rncze',
    count: 1801,
    color: '#5eead4',
  },
  {
    id: 'industry-digital',
    label: '3C 及电器',
    sheetId: '6aYmtl',
    count: 5204,
    color: '#39d8ff',
  },
  {
    id: 'industry-auto',
    label: '汽车',
    sheetId: '7myfJs',
    count: 3221,
    color: '#4f8cff',
  },
  {
    id: 'industry-game',
    label: '游戏',
    sheetId: '8kFWgq',
    count: 29215,
    color: '#8b6cff',
  },
  {
    id: 'industry-commerce',
    label: '互联网电商服务',
    sheetId: '9FoKhW',
    count: 9986,
    color: '#d97cff',
  },
  {
    id: 'industry-finance',
    label: '金融业',
    sheetId: '10chQs',
    count: 2131,
    color: '#94a3b8',
  },
];

export const INDUSTRY_TOTAL = INDUSTRY_OPTIONS.reduce(
  (total, industry) => total + industry.count,
  0,
);
