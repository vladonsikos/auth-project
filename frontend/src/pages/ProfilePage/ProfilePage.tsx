import { zodResolver } from '@hookform/resolvers/zod';
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  Button,
  Alert,
  InputAdornment,
  IconButton,
} from '@mui/material';
import { Visibility, VisibilityOff } from '@mui/icons-material';
import { useMutation } from '@tanstack/react-query';
import { useState, useCallback, useMemo } from 'react';
import { useForm, SubmitHandler } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { toast } from 'react-toastify';
import { z } from 'zod';

import { useAuth } from '../../features/auth/model/useAuth';
import { getErrorMessage } from '../../shared/api/axios';

const createPasswordSchema = (t: (key: string) => string) =>
  z
    .object({
      current_password: z.string().min(1, t('auth.required')),
      new_password: z.string().min(6, t('auth.minPassword')),
      confirm_password: z.string().min(1, t('auth.required')),
    })
    .refine((data) => data.new_password === data.confirm_password, {
      message: t('common.passwordsDoNotMatch'),
      path: ['confirm_password'],
    });

type PasswordForm = z.infer<ReturnType<typeof createPasswordSchema>>;

export const ProfilePage = () => {
  const { user } = useAuth();
  const { t } = useTranslation();
  const [error, setError] = useState<string | null>(null);
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const passwordSchema = useMemo(() => createPasswordSchema(t), [t]);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<PasswordForm>({
    resolver: zodResolver(passwordSchema),
  });

  const changePasswordMutation = useMutation({
    mutationFn: async (data: PasswordForm) => {
      const token = localStorage.getItem('jwt_token');
      const response = await fetch('/api/auth/profile/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          current_password: data.current_password,
          new_password: data.new_password,
          confirm_password: data.confirm_password,
        }),
      });
      if (!response.ok) {
        const err = await response.json();
        throw new Error(
          err.detail || err.current_password || err.confirm_password || 'Failed to change password'
        );
      }
      return response.json();
    },
    onSuccess: () => {
      toast.success(t('profile.passwordUpdated'));
      reset();
      setError(null);
    },
    onError: (err: unknown) => {
      const msg = getErrorMessage(err);
      const errorMap: Record<string, string> = {
        wrong_current_password: t('profile.wrongCurrentPassword'),
        passwords_do_not_match: t('common.passwordsDoNotMatch'),
      };
      setError(errorMap[msg] ?? msg);
    },
  });

  const onSubmit: SubmitHandler<PasswordForm> = useCallback(
    (data) => {
      changePasswordMutation.mutate(data);
    },
    [changePasswordMutation]
  );

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        {t('profile.title')}
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            {user?.first_name} {user?.last_name}
          </Typography>
          <Typography color="text.secondary">{user?.email}</Typography>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            {t('profile.changePassword')}
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          <Box
            component="form"
            onSubmit={handleSubmit(onSubmit)}
            sx={{ display: 'grid', gap: 2, mt: 2 }}
          >
            <TextField
              {...register('current_password')}
              id="current-password"
              name="current_password"
              autoComplete="current-password"
              label={t('profile.currentPassword')}
              type={showCurrentPassword ? 'text' : 'password'}
              fullWidth
              error={!!errors.current_password}
              helperText={errors.current_password?.message}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                      edge="end"
                    >
                      {showCurrentPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
            <TextField
              {...register('new_password')}
              id="new-password"
              name="new_password"
              autoComplete="new-password"
              label={t('profile.newPassword')}
              type={showNewPassword ? 'text' : 'password'}
              fullWidth
              error={!!errors.new_password}
              helperText={errors.new_password?.message}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton onClick={() => setShowNewPassword(!showNewPassword)} edge="end">
                      {showNewPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
            <TextField
              {...register('confirm_password')}
              id="confirm-password"
              name="confirm_password"
              autoComplete="new-password"
              label={t('profile.confirmPassword')}
              type={showConfirmPassword ? 'text' : 'password'}
              fullWidth
              error={!!errors.confirm_password}
              helperText={errors.confirm_password?.message}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      edge="end"
                    >
                      {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
            <Button
              type="submit"
              variant="contained"
              sx={{ mt: 2 }}
              disabled={changePasswordMutation.isPending}
            >
              {changePasswordMutation.isPending ? t('common.loading') : t('profile.changePassword')}
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};
