import { People as PeopleIcon, Badge as BadgeIcon } from '@mui/icons-material';
import { Box, Typography, Card, CardContent, Grid } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';

import { getRoles } from '../../entities/role/api/roleApi';
import { getUsers } from '../../entities/user/api/userApi';

export const DashboardPage = () => {
  const { t } = useTranslation();

  const { data: usersData } = useQuery({
    queryKey: ['users'],
    queryFn: () => getUsers(1, 100),
    retry: false,
  });

  const { data: rolesData } = useQuery({
    queryKey: ['roles'],
    queryFn: () => getRoles(1, 100),
    retry: false,
  });

  const stats = useMemo(
    () => [
      {
        title: t('dashboard.totalUsers'),
        value: usersData?.count ?? 0,
        icon: <PeopleIcon sx={{ fontSize: 48, color: 'primary.main' }} />,
      },
      {
        title: t('dashboard.totalRoles'),
        value: rolesData?.count ?? 0,
        icon: <BadgeIcon sx={{ fontSize: 48, color: 'secondary.main' }} />,
      },
    ],
    [usersData?.count, rolesData?.count, t]
  );

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        {t('dashboard.title')}
      </Typography>
      <Typography variant="body1" color="text.secondary" mb={4}>
        {t('dashboard.welcome')}
      </Typography>

      <Grid container spacing={3}>
        {stats.map((stat) => (
          <Grid item xs={12} sm={6} key={stat.title}>
            <Card>
              <CardContent>
                <Box
                  sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
                >
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      {stat.title}
                    </Typography>
                    <Typography variant="h3">{stat.value}</Typography>
                  </Box>
                  {stat.icon}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};
