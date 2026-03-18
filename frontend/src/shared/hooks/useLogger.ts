import axios from 'axios';

type LogAction =
  | 'login'
  | 'logout'
  | 'create_user'
  | 'update_user'
  | 'delete_user'
  | 'create_role'
  | 'update_role'
  | 'delete_role'
  | string;

interface LogEntry {
  action: LogAction;
  data: Record<string, unknown>;
  timestamp: string;
}

export const useLogger = () => {
  const log = (action: LogAction, data: Record<string, unknown> = {}) => {
    const entry: LogEntry = {
      action,
      data,
      timestamp: new Date().toISOString(),
    };

    console.log('[ACTION LOG]', entry);

    const token = localStorage.getItem('jwt_token');
    if (token) {
      axios
        .post('/api/logs/', entry, {
          headers: { Authorization: `Bearer ${token}` },
          validateStatus: () => true,
        })
        .catch(() => {});
    }
  };

  return { log };
};
