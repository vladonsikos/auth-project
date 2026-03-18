import { zodResolver } from '@hookform/resolvers/zod';
import {
  Search as SearchIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Visibility,
  VisibilityOff,
} from '@mui/icons-material';
import {
  Box,
  Typography,
  Button,
  TextField,
  InputAdornment,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
} from '@mui/material';
import { GridColDef, GridPaginationModel } from '@mui/x-data-grid';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState, useCallback, useMemo, useEffect } from 'react';
import { useForm, SubmitHandler } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { toast } from 'react-toastify';
import { z } from 'zod';

import { getRoles } from '../../entities/role/api/roleApi';
import {
  getUsers,
  createUser,
  updateUser,
  deleteUser,
  bulkDeleteUsers,
} from '../../entities/user/api/userApi';
import { getErrorMessage } from '../../shared/api/axios';
import { useLogger } from '../../shared/hooks/useLogger';
import type { User, Role } from '../../shared/types';
import { ConfirmDialog } from '../../shared/ui/ConfirmDialog';
import { DataTable } from '../../shared/ui/DataTable';

const createUserSchema = (t: (key: string) => string, isEdit: boolean = false) => {
  const requiredMsg = t('auth.required') || 'Required';
  const invalidEmailMsg = t('auth.invalidEmail') || 'Invalid email';
  const minPasswordMsg = t('auth.minPassword') || 'Password must be at least 6 characters';
  const passwordsDoNotMatchMsg = t('common.passwordsDoNotMatch') || 'Passwords do not match';

  return z
    .object({
      first_name: z.string().refine((val) => val.length >= 1, requiredMsg),
      last_name: z.string().refine((val) => val.length >= 1, requiredMsg),
      patronymic: z.string().optional(),
      email: z.string().refine((val) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val), invalidEmailMsg),
      password: isEdit
        ? z
            .string()
            .refine((val) => !val || val.length >= 6, minPasswordMsg)
            .optional()
        : z.string().refine((val) => val && val.length >= 6, minPasswordMsg),
      password_confirm: isEdit
        ? z
            .string()
            .refine((val) => !val || val.length >= 1, requiredMsg)
            .optional()
        : z.string().refine((val) => val && val.length >= 1, requiredMsg),
    })
    .refine(
      (data) => !data.password || !data.password_confirm || data.password === data.password_confirm,
      { message: passwordsDoNotMatchMsg, path: ['password_confirm'] }
    );
};

type UserForm = z.infer<ReturnType<typeof createUserSchema>> & {
  role?: number;
  is_active?: boolean;
};

interface UserRow extends User {
  roleName?: string;
}

export const UsersPage = () => {
  const [search, setSearch] = useState('');
  const [paginationModel, setPaginationModel] = useState<GridPaginationModel>({
    pageSize: 10,
    page: 0,
  });
  const [selectedUser, setSelectedUser] = useState<UserRow | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [roleFilter, setRoleFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const queryClient = useQueryClient();
  const { log } = useLogger();
  const { t } = useTranslation();

  const { data, isLoading } = useQuery({
    queryKey: [
      'users',
      paginationModel.page,
      paginationModel.pageSize,
      search,
      roleFilter,
      statusFilter,
    ],
    queryFn: ({ queryKey }) => {
      const [, page, pageSize, searchValue, role, isActive] = queryKey;
      return getUsers((page as number) + 1, pageSize as number, searchValue as string, {
        role: role as string,
        is_active: isActive as string,
      });
    },
    retry: 3,
    retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 30000),
  });

  const { data: rolesData } = useQuery({
    queryKey: ['roles'],
    queryFn: () => getRoles(1, 100),
    retry: false,
  });

  const users = (data?.results ?? []) as UserRow[];
  const rowCount = data?.count ?? 0;
  const roles = Array.isArray(rolesData?.results) ? (rolesData.results as Role[]) : [];

  const createMutation = useMutation({
    mutationFn: createUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      toast.success(t('common.success'));
      log('create_user');
      setIsFormOpen(false);
    },
    onError: (err: unknown) => toast.error(getErrorMessage(err)),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<UserForm> }) => updateUser(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      toast.success(t('common.success'));
      log('update_user');
      setIsFormOpen(false);
    },
    onError: (err: unknown) => toast.error(getErrorMessage(err)),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      toast.success(t('common.success'));
      log('delete_user', { userId: selectedUser?.id });
      setIsDeleteDialogOpen(false);
      setSelectedUser(null);
    },
    onError: (err: unknown) => toast.error(getErrorMessage(err)),
  });

  const bulkDeleteMutation = useMutation({
    mutationFn: bulkDeleteUsers,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      toast.success(t('common.success'));
      log('delete_user', { count: selectedIds.length });
      setSelectedIds([]);
    },
    onError: (err: unknown) => toast.error(getErrorMessage(err)),
  });

  const handleEdit = useCallback((user: UserRow) => {
    setSelectedUser(user);
    setIsFormOpen(true);
  }, []);

  const handleDeleteClick = useCallback((user: UserRow) => {
    setSelectedUser(user);
    setIsDeleteDialogOpen(true);
  }, []);

  const handleBulkDelete = useCallback(() => {
    if (selectedIds.length > 0) bulkDeleteMutation.mutate(selectedIds);
  }, [selectedIds, bulkDeleteMutation]);

  const handlePaginationChange = useCallback(
    (model: GridPaginationModel) => {
      if (model.page !== paginationModel.page || model.pageSize !== paginationModel.pageSize) {
        setPaginationModel(model);
      }
    },
    [paginationModel]
  );

  const columns: GridColDef[] = useMemo(
    () => [
      { field: 'id', headerName: 'ID', width: 70 },
      {
        field: 'name',
        headerName: t('users.firstName'),
        width: 200,
        valueGetter: (params) => `${params.row.first_name} ${params.row.last_name}`,
      },
      { field: 'email', headerName: t('users.email'), width: 250 },
      {
        field: 'roles',
        headerName: t('users.role'),
        width: 200,
        valueGetter: (params) => params.row.roles?.map((r: Role) => r.name).join(', ') || '',
        renderCell: (params) => (
          <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
            {params.row.roles?.map((role: Role) => (
              <Chip key={role.id} label={role.name} size="small" />
            ))}
          </Box>
        ),
      },
      {
        field: 'is_active',
        headerName: t('users.status'),
        width: 120,
        renderCell: (params) => (
          <Chip
            label={params.value ? t('users.active') : t('users.inactive')}
            color={params.value ? 'success' : 'default'}
            size="small"
          />
        ),
      },
      {
        field: 'actions',
        headerName: t('users.actions'),
        width: 200,
        sortable: false,
        renderCell: (params) => (
          <Box
            sx={{
              display: 'flex',
              gap: 1,
              alignItems: 'center',
              height: '100%',
              position: 'relative',
              zIndex: 1,
            }}
          >
            <Button
              size="small"
              variant="outlined"
              onClick={(e) => {
                e.stopPropagation();
                handleEdit(params.row);
              }}
              sx={{ whiteSpace: 'nowrap', minWidth: 'auto', px: 1 }}
            >
              {t('common.edit')}
            </Button>
            <Button
              size="small"
              variant="contained"
              color="error"
              onClick={(e) => {
                e.stopPropagation();
                handleDeleteClick(params.row);
              }}
              sx={{ whiteSpace: 'nowrap', minWidth: 'auto', px: 1 }}
            >
              {t('common.delete')}
            </Button>
          </Box>
        ),
      },
    ],
    [t, handleEdit, handleDeleteClick]
  );

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">{t('users.title')}</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => {
            setSelectedUser(null);
            setIsFormOpen(true);
          }}
        >
          {t('users.addUser')}
        </Button>
      </Box>

      <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap', alignItems: 'center' }}>
        <TextField
          placeholder={t('common.search')}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
          sx={{ minWidth: 250 }}
        />
        <TextField
          select
          SelectProps={{ native: true }}
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          sx={{ minWidth: 150 }}
        >
          <option value="">{t('users.role')}</option>
          {roles.map((role) => (
            <option key={role.id} value={role.id}>
              {role.name}
            </option>
          ))}
        </TextField>
        <TextField
          select
          SelectProps={{ native: true }}
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          sx={{ minWidth: 120 }}
        >
          <option value="">{t('users.status')}</option>
          <option value="true">{t('users.active')}</option>
          <option value="false">{t('users.inactive')}</option>
        </TextField>
        {selectedIds.length > 0 && (
          <Button
            variant="contained"
            color="error"
            startIcon={<DeleteIcon />}
            onClick={handleBulkDelete}
          >
            {t('common.delete')} ({selectedIds.length})
          </Button>
        )}
      </Box>

      <DataTable
        rows={users}
        columns={columns}
        rowCount={rowCount}
        loading={isLoading}
        paginationModel={paginationModel}
        onPaginationModelChange={handlePaginationChange}
        checkboxSelection
        rowSelectionModel={selectedIds}
        onRowSelectionModelChange={(model) => setSelectedIds(model as number[])}
        exportFileName="users-export"
      />

      <UserFormDialog
        open={isFormOpen}
        onClose={() => setIsFormOpen(false)}
        user={selectedUser}
        onSubmit={(formData) => {
          if (selectedUser) {
            updateMutation.mutate({
              id: selectedUser.id,
              data: {
                first_name: formData.first_name,
                last_name: formData.last_name,
                patronymic: formData.patronymic || '',
                email: formData.email,
                is_active: formData.is_active,
                role: formData.role,
              },
            });
          } else {
            createMutation.mutate({
              first_name: formData.first_name,
              last_name: formData.last_name,
              patronymic: formData.patronymic || '',
              email: formData.email,
              password: formData.password || '',
              password_confirm: formData.password_confirm || '',
            });
          }
        }}
        isSubmitting={createMutation.isPending || updateMutation.isPending}
        t={t}
        roles={roles}
      />

      <ConfirmDialog
        open={isDeleteDialogOpen}
        title={t('users.deleteUser')}
        message={t('users.deleteConfirm', {
          name: `${selectedUser?.first_name} ${selectedUser?.last_name}`,
        })}
        confirmText={t('common.delete')}
        onConfirm={() => selectedUser && deleteMutation.mutate(selectedUser.id)}
        onCancel={() => setIsDeleteDialogOpen(false)}
        loading={deleteMutation.isPending}
      />
    </Box>
  );
};

interface UserFormDialogProps {
  open: boolean;
  onClose: () => void;
  user: UserRow | null;
  onSubmit: (data: UserForm & { role?: number; is_active?: boolean }) => void;
  isSubmitting: boolean;
  t: (key: string) => string;
  roles: Role[];
}

const UserFormDialog = ({
  open,
  onClose,
  user,
  onSubmit,
  isSubmitting,
  t,
  roles,
}: UserFormDialogProps) => {
  const [showPassword, setShowPassword] = useState(false);
  const [showPasswordConfirm, setShowPasswordConfirm] = useState(false);
  const [selectedRole, setSelectedRole] = useState<number>(user?.roles?.[0]?.id || 3);
  const [isActive, setIsActive] = useState(user?.is_active ?? true);

  const isEdit = !!user;
  const schema = useMemo(() => createUserSchema(t, isEdit), [t, isEdit]);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<UserForm>({
    resolver: zodResolver(schema),
    defaultValues: { first_name: '', last_name: '', patronymic: '', email: '' },
  });

  useEffect(() => {
    if (user) {
      reset({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        patronymic: user.patronymic || '',
        email: user.email || '',
      });
      setSelectedRole(user.roles?.[0]?.id || 3);
      setIsActive(user.is_active ?? true);
    } else {
      reset({ first_name: '', last_name: '', patronymic: '', email: '' });
      setSelectedRole(3);
      setIsActive(true);
    }
  }, [user, reset]);

  const submitHandler: SubmitHandler<UserForm> = (data) => {
    onSubmit({ ...data, role: selectedRole, is_active: isActive });
  };

  return (
    <Dialog open={open} onClose={isSubmitting ? undefined : onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{user ? t('users.editUser') : t('users.addUser')}</DialogTitle>
      <form onSubmit={handleSubmit(submitHandler)}>
        <DialogContent>
          <Box sx={{ display: 'grid', gap: 2, mt: 1 }}>
            <TextField
              {...register('first_name')}
              label={t('users.firstName')}
              fullWidth
              error={!!errors.first_name}
              helperText={errors.first_name?.message}
              disabled={isSubmitting}
            />
            <TextField
              {...register('last_name')}
              label={t('users.lastName')}
              fullWidth
              error={!!errors.last_name}
              helperText={errors.last_name?.message}
              disabled={isSubmitting}
            />
            <TextField
              {...register('patronymic')}
              label={t('users.patronymic')}
              fullWidth
              disabled={isSubmitting}
            />
            <TextField
              {...register('email')}
              label={t('users.email')}
              type="email"
              fullWidth
              error={!!errors.email}
              helperText={errors.email?.message}
              disabled={isSubmitting}
            />
            {user && (
              <>
                <FormControl fullWidth>
                  <InputLabel>{t('users.role')}</InputLabel>
                  <Select
                    value={selectedRole}
                    label={t('users.role')}
                    onChange={(e) => setSelectedRole(Number(e.target.value))}
                    disabled={isSubmitting}
                  >
                    {roles.map((role) => (
                      <MenuItem key={role.id} value={role.id}>
                        {role.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <FormControlLabel
                  control={
                    <Switch
                      checked={isActive}
                      onChange={(e) => setIsActive(e.target.checked)}
                      disabled={isSubmitting}
                    />
                  }
                  label={isActive ? t('users.active') : t('users.inactive')}
                />
              </>
            )}
            {!user && (
              <>
                <TextField
                  {...register('password')}
                  label={t('auth.password')}
                  type={showPassword ? 'text' : 'password'}
                  fullWidth
                  error={!!errors.password}
                  helperText={errors.password?.message}
                  disabled={isSubmitting}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton onClick={() => setShowPassword(!showPassword)} edge="end">
                          {showPassword ? <VisibilityOff /> : <Visibility />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                />
                <TextField
                  {...register('password_confirm')}
                  label={t('profile.confirmPassword')}
                  type={showPasswordConfirm ? 'text' : 'password'}
                  fullWidth
                  error={!!errors.password_confirm}
                  helperText={errors.password_confirm?.message}
                  disabled={isSubmitting}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          onClick={() => setShowPasswordConfirm(!showPasswordConfirm)}
                          edge="end"
                        >
                          {showPasswordConfirm ? <VisibilityOff /> : <Visibility />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                />
              </>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose} disabled={isSubmitting}>
            {t('common.cancel')}
          </Button>
          <Button type="submit" variant="contained" disabled={isSubmitting}>
            {isSubmitting ? t('common.loading') : user ? t('common.update') : t('common.create')}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};
