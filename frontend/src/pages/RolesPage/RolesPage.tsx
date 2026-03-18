import { zodResolver } from '@hookform/resolvers/zod';
import {
  Add as AddIcon,
  Security as SecurityIcon,
  MoreVert as MoreVertIcon,
} from '@mui/icons-material';
import {
  Box,
  Typography,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tab,
  Tabs,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Checkbox,
  CircularProgress,
  IconButton,
  Menu,
  MenuItem,
  ListItemIcon,
} from '@mui/material';
import { GridColDef, GridPaginationModel } from '@mui/x-data-grid';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState, useCallback, useMemo, useEffect } from 'react';
import { useForm, SubmitHandler } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { toast } from 'react-toastify';
import { z } from 'zod';

import {
  getAccessRules,
  getBusinessElements,
  createAccessRule,
  updateAccessRule,
} from '../../entities/access/api/accessRuleApi';
import type { AccessRule, BusinessElement, AccessRuleInput } from '../../entities/access/types';
import { getRoles, createRole, updateRole, deleteRole } from '../../entities/role/api/roleApi';
import { getErrorMessage } from '../../shared/api/axios';
import { useLogger } from '../../shared/hooks/useLogger';
import { ConfirmDialog } from '../../shared/ui/ConfirmDialog';
import { DataTable } from '../../shared/ui/DataTable';
import { AccessRuleDialog } from '../../widgets/AccessRuleDialog/AccessRuleDialog';

// Schema factory function for translated validation
const createRoleSchema = (t: (key: string) => string) =>
  z.object({
    name: z.string().min(1, t('auth.required') || 'Required'),
    description: z.string().optional(),
  });

type RoleForm = z.infer<ReturnType<typeof createRoleSchema>>;

interface RoleRow {
  id: number;
  name: string;
  description: string;
}

export const RolesPage = () => {
  const [paginationModel, setPaginationModel] = useState<GridPaginationModel>({
    pageSize: 10,
    page: 0,
  });
  const [selectedRole, setSelectedRole] = useState<RoleRow | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [isAccessDialogOpen, setIsAccessDialogOpen] = useState(false);
  const [menuPosition, setMenuPosition] = useState<{ top: number; left: number } | null>(null);
  const [currentRow, setCurrentRow] = useState<RoleRow | null>(null);
  const queryClient = useQueryClient();
  const { log } = useLogger();
  const { t } = useTranslation();

  const { data, isLoading } = useQuery({
    queryKey: ['roles', paginationModel.page + 1, paginationModel.pageSize],
    queryFn: ({ queryKey }) => {
      const [, page, pageSize] = queryKey;
      return getRoles(page as number, pageSize as number);
    },
    retry: 3,
    retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 30000),
  });

  const roles = (data?.results ?? []) as RoleRow[];
  const rowCount = data?.count ?? 0;

  const createMutation = useMutation({
    mutationFn: createRole,
    onSuccess: (newRole) => {
      queryClient.invalidateQueries({ queryKey: ['roles'] });
      toast.success(t('common.success'));
      log('create_role');
      setIsFormOpen(false);
      // Open access rules dialog for the newly created role
      setSelectedRole({
        id: newRole.id,
        name: newRole.name,
        description: newRole.description || '',
      });
      setIsAccessDialogOpen(true);
    },
    onError: (err: unknown) => {
      toast.error(getErrorMessage(err));
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<RoleForm> }) => updateRole(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roles'] });
      toast.success(t('common.success'));
      log('update_role');
      setIsFormOpen(false);
    },
    onError: (err: unknown) => {
      toast.error(getErrorMessage(err));
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteRole,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roles'] });
      toast.success(t('common.success'));
      log('delete_role', { roleId: selectedRole?.id });
      setIsDeleteDialogOpen(false);
      setSelectedRole(null);
    },
    onError: (err: unknown) => {
      toast.error(getErrorMessage(err));
    },
  });

  const handleEdit = useCallback((role: RoleRow) => {
    setSelectedRole(role);
    setIsFormOpen(true);
  }, []);

  const handleDeleteClick = useCallback((role: RoleRow) => {
    setSelectedRole(role);
    setIsDeleteDialogOpen(true);
  }, []);

  const handleAccessRules = useCallback((role: RoleRow) => {
    setSelectedRole(role);
    setIsAccessDialogOpen(true);
  }, []);

  const handlePaginationChange = useCallback(
    (model: GridPaginationModel) => {
      if (model.page !== paginationModel.page || model.pageSize !== paginationModel.pageSize) {
        setPaginationModel(model);
      }
    },
    [paginationModel]
  );

  // Handle action menu
  const handleActionMenuOpen = useCallback((event: React.MouseEvent<HTMLElement>, row: RoleRow) => {
    const rect = event.currentTarget.getBoundingClientRect();
    setMenuPosition({ top: rect.bottom + window.scrollY, left: rect.right + window.scrollX });
    setCurrentRow(row);
  }, []);

  const handleActionMenuClose = useCallback(() => {
    setMenuPosition(null);
    setCurrentRow(null);
  }, []);

  const handleMenuAccessRules = useCallback(() => {
    if (currentRow) {
      handleAccessRules(currentRow);
    }
    setMenuPosition(null);
    setCurrentRow(null);
  }, [currentRow, handleAccessRules]);

  const handleMenuEdit = useCallback(() => {
    if (currentRow) {
      handleEdit(currentRow);
    }
    setMenuPosition(null);
    setCurrentRow(null);
  }, [currentRow, handleEdit]);

  const handleMenuDelete = useCallback(() => {
    if (currentRow) {
      handleDeleteClick(currentRow);
    }
    setMenuPosition(null);
    setCurrentRow(null);
  }, [currentRow, handleDeleteClick]);

  const columns: GridColDef[] = useMemo(
    () => [
      { field: 'id', headerName: 'ID', width: 70 },
      { field: 'name', headerName: t('roles.name'), width: 200 },
      { field: 'description', headerName: t('roles.description'), width: 400 },
      {
        field: 'actions',
        headerName: t('users.actions'),
        width: 80,
        sortable: false,
        renderCell: (params) => (
            <IconButton
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                handleActionMenuOpen(e, params.row);
              }}
              sx={{ p: 0.5 }}
            >
              <MoreVertIcon />
            </IconButton>
          ),
      },
    ],
    [t, handleActionMenuOpen]
  );

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">{t('roles.title')}</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => {
            setSelectedRole(null);
            setIsFormOpen(true);
          }}
        >
          {t('roles.addRole')}
        </Button>
      </Box>

      <DataTable
        rows={roles}
        columns={columns}
        rowCount={rowCount}
        loading={isLoading}
        paginationModel={paginationModel}
        onPaginationModelChange={handlePaginationChange}
        exportFileName="roles-export"
      />

      <RoleFormDialog
        open={isFormOpen}
        onClose={() => setIsFormOpen(false)}
        role={selectedRole}
        onSubmit={(formData) => {
          if (selectedRole) {
            updateMutation.mutate({ id: selectedRole.id, data: formData });
          } else {
            createMutation.mutate(formData);
          }
        }}
        isSubmitting={createMutation.isPending || updateMutation.isPending}
        t={t}
      />

      <ConfirmDialog
        open={isDeleteDialogOpen}
        title={t('roles.deleteRole')}
        message={t('roles.deleteConfirm', { name: selectedRole?.name || '' })}
        confirmText={t('common.delete')}
        onConfirm={() => selectedRole && deleteMutation.mutate(selectedRole.id)}
        onCancel={() => setIsDeleteDialogOpen(false)}
        loading={deleteMutation.isPending}
      />

      <AccessRuleDialog
        open={isAccessDialogOpen}
        onClose={() => setIsAccessDialogOpen(false)}
        roleId={selectedRole?.id || 0}
        roleName={selectedRole?.name || ''}
      />

      {/* Action Menu */}
      <Menu
        open={Boolean(menuPosition)}
        onClose={handleActionMenuClose}
        anchorReference="anchorPosition"
        anchorPosition={menuPosition ?? undefined}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <MenuItem onClick={handleMenuAccessRules}>
          <ListItemIcon>
            <SecurityIcon fontSize="small" />
          </ListItemIcon>
          {t('roles.rights')}
        </MenuItem>
        <MenuItem onClick={handleMenuEdit}>
          <ListItemIcon>
            <SecurityIcon fontSize="small" sx={{ visibility: 'hidden' }} />
          </ListItemIcon>
          {t('common.edit')}
        </MenuItem>
        <MenuItem onClick={handleMenuDelete} sx={{ color: 'error.main' }}>
          <ListItemIcon>
            <SecurityIcon fontSize="small" sx={{ visibility: 'hidden' }} />
          </ListItemIcon>
          {t('common.delete')}
        </MenuItem>
      </Menu>
    </Box>
  );
};

interface RoleFormDialogProps {
  open: boolean;
  onClose: () => void;
  role: RoleRow | null;
  onSubmit: (data: RoleForm) => void;
  isSubmitting: boolean;
  t: (key: string) => string;
}

const RoleFormDialog = ({
  open,
  onClose,
  role,
  onSubmit,
  isSubmitting,
  t,
}: RoleFormDialogProps) => {
  const [tab, setTab] = useState(0);
  const queryClient = useQueryClient();
  const schema = useMemo(() => createRoleSchema(t), [t]);
  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
    reset,
  } = useForm<RoleForm>({
    resolver: zodResolver(schema),
    defaultValues: { name: '', description: '' },
  });

  // Reset form when role changes
  useEffect(() => {
    if (role) {
      reset({ name: role.name, description: role.description });
    } else {
      reset({ name: '', description: '' });
    }
  }, [role, reset]);

  // Fetch business elements and existing rules (for edit mode)
  const { data: elements, isLoading: elementsLoading } = useQuery({
    queryKey: ['businessElements'],
    queryFn: getBusinessElements,
    enabled: open,
  });

  const { data: rules, isLoading: rulesLoading } = useQuery({
    queryKey: ['accessRules', role?.id],
    queryFn: () => (role?.id ? getAccessRules(role.id) : Promise.resolve([])),
    enabled: open && !!role?.id,
  });

  const createRuleMutation = useMutation({
    mutationFn: (data: AccessRuleInput) => createAccessRule(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accessRules'] });
    },
  });

  const updateRuleMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<AccessRuleInput> }) =>
      updateAccessRule(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accessRules'] });
    },
  });

  // Build rules map for the form
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
      updateRuleMutation.mutate({ id: ruleId, data: { [field]: value } });
    } else if (value) {
      // Only create rule if checking a box
      createRuleMutation.mutate({
        role: role!.id,
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

  const submitHandler: SubmitHandler<RoleForm> = (data) => {
    onSubmit(data);
  };

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTab(newValue);
  };

  const isLoading = elementsLoading || rulesLoading;

  return (
    <Dialog open={open} onClose={isSubmitting ? undefined : onClose} maxWidth="lg" fullWidth>
      <DialogTitle>{role ? t('roles.editRole') : t('roles.addRole')}</DialogTitle>
      <Tabs value={tab} onChange={handleTabChange} sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tab label={t('roles.tabBasic')} />
        <Tab label={t('roles.tabRights')} />
      </Tabs>
      <form onSubmit={handleSubmit(submitHandler)}>
        <DialogContent>
          {tab === 0 && (
            <Box sx={{ display: 'grid', gap: 2, mt: 2 }}>
              <TextField
                {...register('name')}
                id="role-name"
                name="name"
                autoComplete="off"
                label={t('roles.name')}
                fullWidth
                error={!!errors.name}
                helperText={errors.name?.message}
                disabled={isSubmitting}
              />
              <TextField
                {...register('description')}
                id="role-description"
                name="description"
                autoComplete="off"
                label={t('roles.description')}
                fullWidth
                multiline
                rows={4}
                disabled={isSubmitting}
              />
            </Box>
          )}
          {tab === 1 && (
            <Box sx={{ mt: 2 }}>
              {!role ? (
                <Typography variant="body2" color="text.secondary" mb={2}>
                  {t('roles.rightsInfoText')}
                </Typography>
              ) : (
                <Typography variant="body2" color="text.secondary" mb={2}>
                  {t('access.rulesDescription')}
                </Typography>
              )}

              {isLoading ? (
                <CircularProgress />
              ) : (
                <TableContainer component={Paper}>
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
                                  handlePermissionChange(
                                    rule?.id,
                                    element.id,
                                    'read',
                                    e.target.checked
                                  )
                                }
                                disabled={!role}
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
                                disabled={!role}
                              />
                            </TableCell>
                            <TableCell align="center">
                              <Checkbox
                                checked={rule?.create || false}
                                onChange={(e) =>
                                  handlePermissionChange(
                                    rule?.id,
                                    element.id,
                                    'create',
                                    e.target.checked
                                  )
                                }
                                disabled={!role}
                              />
                            </TableCell>
                            <TableCell align="center">
                              <Checkbox
                                checked={rule?.update || false}
                                onChange={(e) =>
                                  handlePermissionChange(
                                    rule?.id,
                                    element.id,
                                    'update',
                                    e.target.checked
                                  )
                                }
                                disabled={!role}
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
                                disabled={!role}
                              />
                            </TableCell>
                            <TableCell align="center">
                              <Checkbox
                                checked={rule?.delete || false}
                                onChange={(e) =>
                                  handlePermissionChange(
                                    rule?.id,
                                    element.id,
                                    'delete',
                                    e.target.checked
                                  )
                                }
                                disabled={!role}
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
                                disabled={!role}
                              />
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          {tab === 0 ? (
            <>
              <Button onClick={onClose} disabled={isSubmitting}>
                {t('common.cancel')}
              </Button>
              <Button
                type="button"
                variant="outlined"
                onClick={() => setTab(1)}
                disabled={isSubmitting || !watch('name')}
              >
                {t('common.next')}
              </Button>
            </>
          ) : (
            <>
              <Button
                type="button"
                variant="outlined"
                onClick={() => setTab(0)}
                disabled={isSubmitting}
              >
                {t('common.back')}
              </Button>
              <Button type="submit" variant="contained" disabled={isSubmitting}>
                {isSubmitting
                  ? t('common.loading')
                  : role
                    ? t('common.update')
                    : t('common.create')}
              </Button>
            </>
          )}
        </DialogActions>
      </form>
    </Dialog>
  );
};
