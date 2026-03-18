import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Checkbox,
  CircularProgress,
} from '@mui/material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';

import {
  getAccessRules,
  getBusinessElements,
  updateAccessRule,
  createAccessRule,
} from '../../entities/access/api/accessRuleApi';
import type { AccessRule, BusinessElement, AccessRuleInput } from '../../entities/access/types';

interface AccessRuleDialogProps {
  open: boolean;
  onClose: () => void;
  roleId: number;
  roleName: string;
}

export const AccessRuleDialog = ({ open, onClose, roleId, roleName }: AccessRuleDialogProps) => {
  const queryClient = useQueryClient();
  const { t } = useTranslation();

  const { data: rules, isLoading: rulesLoading } = useQuery({
    queryKey: ['accessRules', roleId],
    queryFn: () => getAccessRules(roleId),
    enabled: open,
  });

  const { data: elements, isLoading: elementsLoading } = useQuery({
    queryKey: ['businessElements'],
    queryFn: getBusinessElements,
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<AccessRule> }) =>
      updateAccessRule(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accessRules', roleId] });
    },
  });

  const createMutation = useMutation({
    mutationFn: (data: AccessRuleInput) => createAccessRule({ ...data, role: roleId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accessRules', roleId] });
    },
  });

  const rulesByElement = useMemo(() => {
    const map = new Map<number, AccessRule>();
    rules?.forEach((rule) => map.set(rule.element, rule));
    return map;
  }, [rules]);

  const handlePermissionChange = (
    ruleId: number | undefined,
    elementId: number,
    field: keyof AccessRule,
    value: boolean
  ) => {
    if (ruleId) {
      updateMutation.mutate({ id: ruleId, data: { [field]: value } });
    } else {
      // Create new rule with this permission
      createMutation.mutate({
        role: roleId,
        element: elementId,
        [field]: value,
        read: field === 'read' ? value : false,
        read_all: field === 'read_all' ? value : false,
        create: field === 'create' ? value : false,
        update: field === 'update' ? value : false,
        update_all: field === 'update_all' ? value : false,
        delete: field === 'delete' ? value : false,
        delete_all: field === 'delete_all' ? value : false,
      });
    }
  };

  const isLoading = rulesLoading || elementsLoading;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>{t('access.rulesForRole', { role: roleName })}</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" mb={2}>
          {t('access.rulesDescription')}
        </Typography>

        {isLoading ? (
          <CircularProgress />
        ) : (
          <TableContainer component={Paper} sx={{ mt: 2 }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>{t('access.element')}</TableCell>
                  <TableCell align="center">{t('access.read')}</TableCell>
                  <TableCell align="center">{t('access.readAll')}</TableCell>
                  <TableCell align="center">{t('access.create')}</TableCell>
                  <TableCell align="center">{t('access.update')}</TableCell>
                  <TableCell align="center">{t('access.updateAll')}</TableCell>
                  <TableCell align="center">{t('access.delete')}</TableCell>
                  <TableCell align="center">{t('access.deleteAll')}</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {(elements as BusinessElement[])?.map((element) => {
                  const rule = rulesByElement.get(element.id);
                  return (
                    <TableRow key={element.id}>
                      <TableCell>{element.name}</TableCell>
                      <TableCell align="center">
                        <Checkbox
                          checked={rule?.read || false}
                          onChange={(e) =>
                            handlePermissionChange(rule?.id, element.id, 'read', e.target.checked)
                          }
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Checkbox
                          checked={rule?.read_all || false}
                          onChange={(e) =>
                            handlePermissionChange(
                              rule?.id,
                              element.id,
                              'read_all',
                              e.target.checked
                            )
                          }
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Checkbox
                          checked={rule?.create || false}
                          onChange={(e) =>
                            handlePermissionChange(rule?.id, element.id, 'create', e.target.checked)
                          }
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Checkbox
                          checked={rule?.update || false}
                          onChange={(e) =>
                            handlePermissionChange(rule?.id, element.id, 'update', e.target.checked)
                          }
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Checkbox
                          checked={rule?.update_all || false}
                          onChange={(e) =>
                            handlePermissionChange(
                              rule?.id,
                              element.id,
                              'update_all',
                              e.target.checked
                            )
                          }
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Checkbox
                          checked={rule?.delete || false}
                          onChange={(e) =>
                            handlePermissionChange(rule?.id, element.id, 'delete', e.target.checked)
                          }
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Checkbox
                          checked={rule?.delete_all || false}
                          onChange={(e) =>
                            handlePermissionChange(
                              rule?.id,
                              element.id,
                              'delete_all',
                              e.target.checked
                            )
                          }
                        />
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>{t('common.close')}</Button>
      </DialogActions>
    </Dialog>
  );
};
