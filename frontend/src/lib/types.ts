export type Card = {
  id: string;
  title: string;
  details: string;
};

export type Column = {
  id: string;
  name: string;
  cardIds: string[];
};

export type Board = {
  columns: Column[];
  cards: Record<string, Card>;
};
