export interface AccessRule {
  id: number;
  role: number;
  role_name: string;
  element: number;
  element_name: string;
  read: boolean;
  read_all: boolean;
  create: boolean;
  update: boolean;
  update_all: boolean;
  delete: boolean;
  delete_all: boolean;
}

export interface AccessRuleInput {
  role: number;
  element: number;
  read?: boolean;
  read_all?: boolean;
  create?: boolean;
  update?: boolean;
  update_all?: boolean;
  delete?: boolean;
  delete_all?: boolean;
}

export interface BusinessElement {
  id: number;
  name: string;
  description: string;
}
