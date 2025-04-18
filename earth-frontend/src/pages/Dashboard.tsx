import React, { useState, useEffect } from 'react';
import {
  Activity,
  AreaChart as AreaChartIcon,
  Database,
  FileJson,
  RefreshCcw,
  Search,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import AppLayout from '@/components/layout/AppLayout';
import StatsCard from '@/components/cards/StatsCard';
import { useToast } from '@/hooks/use-toast';
import { endpointsApi, schemasApi, managementApi, auditApi } from '@/services/api';
import LoadingSpinner from '@/components/LoadingSpinner';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  BarChart,
  Bar,
  AreaChart,
  Area,
} from 'recharts';

const Dashboard: React.FC = () => {
  const { toast } = useToast();

  const [isReindexing, setIsReindexing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [stats, setStats] = useState({
    schemaCount: 0,
    endpointCount: 0,
    searchCount: 0,
  });

  const [activityData, setActivityData] = useState<
    { date: string; searches: number; endpoints: number; uploads: number }[]
  >([]);

  // Load initial data
  useEffect(() => {
    const loadStats = async () => {
      setIsLoading(true);
      try {
        // Get schemas count
        const schemasResponse = await schemasApi.getSchemas();
        const schemaCount = schemasResponse.data?.length || 0;

        // Get endpoints count for the first schema (if exists)
        let endpointCount = 0;
        if (schemasResponse.data && schemasResponse.data.length > 0) {
          const endpointsResponse = await endpointsApi.getEndpoints(schemasResponse.data[0].id);
          endpointCount = endpointsResponse.data?.length || 0;
        }
        let searchCount = 0;

        // Fetch audit logs by day for activity charts
        const auditRes = await auditApi.getAuditLogsByDay();
        if (auditRes.data) {
          // Optionally, format date for chart display
          setActivityData(
            auditRes.data.map((item) => ({
              date: new Date(item.day).toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
              }),
              searches: item.count,
              endpoints: 0,
              uploads: 0,
            }))
          );

          searchCount = auditRes.data.reduce((acc, item) => acc + item.count, 0);
          setStats({
            schemaCount,
            endpointCount,
            searchCount, // Use the calculated searchCount
          });
        } else {
          setActivityData([]);
        }
      } catch (error) {
        console.error('Error loading dashboard stats:', error);
        toast({
          title: 'Error',
          description: 'Failed to load dashboard statistics',
          variant: 'destructive',
        });
        setActivityData([]);
      } finally {
        setIsLoading(false);
      }
    };

    loadStats();
  }, [toast]);

  const handleReindex = async () => {
    setIsReindexing(true);
    try {
      await managementApi.reindexVectorStore();
      toast({
        title: 'Reindexing Started',
        description: 'Vector store reindexing has been initiated',
      });
    } catch (error) {
      console.error('Error reindexing vector store:', error);
      toast({
        title: 'Reindexing Error',
        description: 'Failed to start vector store reindexing',
        variant: 'destructive',
      });
    } finally {
      setIsReindexing(false);
    }
  };

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
            <p className="text-muted-foreground">Welcome back! Here's an overview of your data.</p>
          </div>
          <Button onClick={handleReindex} disabled={isReindexing}>
            {isReindexing ? (
              <LoadingSpinner size="sm" className="mr-2" />
            ) : (
              <RefreshCcw className="h-4 w-4 mr-2" />
            )}
            Reindex
          </Button>
        </div>

        {isLoading ? (
          <div className="h-40 flex items-center justify-center">
            <LoadingSpinner />
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <StatsCard
              title="Total Schemas"
              value={stats.schemaCount}
              description="Uploaded OpenAPI schemas"
              icon={<FileJson className="h-4 w-4" />}
              variant="primary"
            />
            <StatsCard
              title="API Endpoints"
              value={stats.endpointCount}
              description="Indexed API endpoints"
              icon={<Database className="h-4 w-4" />}
              // trend={{ value: 12, label: 'Increase from last month', direction: 'up' }}
              variant="secondary"
            />
            <StatsCard
              title="Search Queries"
              value={stats.searchCount}
              description="Total queries processed"
              icon={<Search className="h-4 w-4" />}
              // trend={{ value: 8, label: 'Increase from last month', direction: 'up' }}
              variant="accent"
            />
          </div>
        )}

        <Tabs defaultValue="activity">
          <TabsList className="grid w-full md:w-auto grid-cols-2 md:grid-cols-3">
            <TabsTrigger value="activity">
              <Activity className="h-4 w-4 mr-2" />
              Activity
            </TabsTrigger>
            <TabsTrigger value="searches">
              <Search className="h-4 w-4 mr-2" />
              Searches
            </TabsTrigger>
            <TabsTrigger value="usage">
              <AreaChartIcon className="h-4 w-4 mr-2" />
              Usage
            </TabsTrigger>
          </TabsList>

          <TabsContent value="activity" className="pt-4">
            <Card className="glass-card">
              <CardHeader>
                <CardTitle>Activity Overview</CardTitle>
                <CardDescription>
                  View the recent activity across your Planet Earth dashboard
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart
                      data={activityData}
                      margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip />
                      <Line
                        type="monotone"
                        dataKey="searches"
                        stroke="#7c2bc0"
                        strokeWidth={2}
                        activeDot={{ r: 8 }}
                      />
                      <Line type="monotone" dataKey="endpoints" stroke="#00c4cc" strokeWidth={2} />
                      <Line type="monotone" dataKey="uploads" stroke="#0a0118" strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="searches" className="pt-4">
            <Card className="glass-card">
              <CardHeader>
                <CardTitle>Search Metrics</CardTitle>
                <CardDescription>Analysis of semantic search queries over time</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={activityData}
                      margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="searches" fill="#7c2bc0" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="usage" className="pt-4">
            <Card className="glass-card">
              <CardHeader>
                <CardTitle>System Usage</CardTitle>
                <CardDescription>Monitor API usage and system performance</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart
                      data={activityData}
                      margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip />
                      <Area
                        type="monotone"
                        dataKey="endpoints"
                        stroke="#7c2bc0"
                        fill="#7c2bc0"
                        fillOpacity={0.2}
                      />
                      <Area
                        type="monotone"
                        dataKey="uploads"
                        stroke="#00c4cc"
                        fill="#00c4cc"
                        fillOpacity={0.2}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </AppLayout>
  );
};

export default Dashboard;
