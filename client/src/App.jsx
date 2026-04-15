import { useEffect, useState } from 'react'
import {
  App as AntApp,
  Alert,
  Button,
  Card,
  Col,
  ConfigProvider,
  Divider,
  Empty,
  Form,
  Input,
  InputNumber,
  Layout,
  List,
  Popconfirm,
  Row,
  Select,
  Skeleton,
  Slider,
  Space,
  Spin,
  Statistic,
  Switch,
  Tabs,
  Tag,
  Typography,
  message,
} from 'antd'
import {
  CheckCircleFilled,
  DeleteOutlined,
  DownloadOutlined,
  LogoutOutlined,
  ReloadOutlined,
  RocketOutlined,
  SafetyOutlined,
  SendOutlined,
  UserOutlined,
  WalletOutlined,
} from '@ant-design/icons'
import { API_BASE_URL, apiRequest, clearToken, getToken, setToken } from './lib/api'

const { Header, Content } = Layout
const { TextArea } = Input

const initialPrefs = {
  tone: 'professional',
  creativity: 3,
  audience: 'general',
  depth: 'balanced',
  output_format: 'report',
  language: 'English',
  max_sources: 3,
  extra_context: '',
  include_citations: true,
}

const toneOptions = ['professional', 'friendly', 'analytical', 'concise', 'technical']
const audienceOptions = ['general', 'student', 'executive', 'technical', 'researcher']
const formatOptions = ['summary', 'bullet_points', 'report', 'table']
const depthOptions = [
  { value: 'brief', label: 'Brief' },
  { value: 'balanced', label: 'Balanced' },
  { value: 'deep', label: 'Deep' },
]

let razorpayPromise

const fmtDate = (value) => {
  if (!value) return '—'
  const ts = typeof value === 'number' && value < 1e12 ? value * 1000 : value
  const d = new Date(ts)
  return Number.isNaN(d.getTime())
    ? String(value)
    : new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeStyle: 'short' }).format(d)
}

const shortId = (value) => (value ? `${value.slice(0, 6)}…${value.slice(-4)}` : '—')

async function loadRazorpay() {
  if (window.Razorpay) return window.Razorpay
  if (!razorpayPromise) {
    razorpayPromise = new Promise((resolve, reject) => {
      const script = document.createElement('script')
      script.src = 'https://checkout.razorpay.com/v1/checkout.js'
      script.async = true
      script.onload = () => resolve(window.Razorpay)
      script.onerror = () => reject(new Error('Could not load Razorpay checkout'))
      document.body.appendChild(script)
    })
  }
  return razorpayPromise
}

function StatCard({ title, value, icon }) {
  return (
    <Card className="glass-card border-0 shadow-soft">
      <Statistic title={title} value={value} prefix={icon} />
    </Card>
  )
}

function EmptyState({ title, description }) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-200 bg-white/70 p-6 text-center">
      <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={false} />
      <div className="mt-2 font-semibold text-slate-800">{title}</div>
      <div className="mt-1 text-sm text-slate-500">{description}</div>
    </div>
  )
}

export default function App() {
  const [msg, holder] = message.useMessage()
  const [token, setTokenState] = useState(() => getToken())
  const [booting, setBooting] = useState(true)
  const [authMode, setAuthMode] = useState('login')
  const [authLoading, setAuthLoading] = useState(false)
  const [dashboardLoading, setDashboardLoading] = useState(false)
  const [researchLoading, setResearchLoading] = useState(false)
  const [accountLoading, setAccountLoading] = useState(false)
  const [subLoading, setSubLoading] = useState('')
  const [user, setUser] = useState(null)
  const [overview, setOverview] = useState(null)
  const [credits, setCredits] = useState(0)
  const [sessions, setSessions] = useState([])
  const [transactions, setTransactions] = useState([])
  const [subscriptions, setSubscriptions] = useState([])
  const [files, setFiles] = useState([])
  const [billing, setBilling] = useState(null)
  const [researchResult, setResearchResult] = useState(null)
  const [tab, setTab] = useState('research')
  const [authForm] = Form.useForm()
  const [researchForm] = Form.useForm()
  const [profileForm] = Form.useForm()
  const [passwordForm] = Form.useForm()

  const loadDashboard = async (currentToken = token) => {
    if (!currentToken) return
    setDashboardLoading(true)
    try {
      const [me, creditsData, overviewData, sessionsData, txData, subData, filesData, billingData] =
        await Promise.all([
          apiRequest('/auth/me', { token: currentToken }),
          apiRequest('/research/credits/me', { token: currentToken }),
          apiRequest('/account/overview', { token: currentToken }),
          apiRequest('/research/sessions?limit=10', { token: currentToken }),
          apiRequest('/account/transactions', { token: currentToken }),
          apiRequest('/account/subscriptions', { token: currentToken }),
          apiRequest('/account/files', { token: currentToken }),
          apiRequest('/billing/config', { token: currentToken }),
        ])

      setUser(me)
      setCredits(creditsData.credits)
      setOverview(overviewData)
      setSessions(sessionsData.sessions || [])
      setTransactions(txData.transactions || [])
      setSubscriptions(subData.subscriptions || [])
      setFiles(filesData.files || [])
      setBilling(billingData)
      profileForm.setFieldsValue({ name: me.name })
    } catch (error) {
      clearToken()
      setTokenState(null)
      setUser(null)
      msg.error(error.message)
    } finally {
      setDashboardLoading(false)
      setBooting(false)
    }
  }

  useEffect(() => {
    if (!token) {
      setBooting(false)
      return
    }
    loadDashboard(token)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token])

  const onAuth = async (values) => {
    setAuthLoading(true)
    try {
      const payload =
        authMode === 'register'
          ? { name: values.name, email: values.email, password: values.password }
          : { email: values.email, password: values.password }
      const res = await apiRequest(`/auth/${authMode}`, {
        method: 'POST',
        body: payload,
      })
      setToken(res.access_token)
      setTokenState(res.access_token)
      setUser(res.user)
      msg.success(authMode === 'register' ? 'Account created' : 'Signed in')
      await loadDashboard(res.access_token)
      setTab('research')
    } catch (error) {
      msg.error(error.message)
    } finally {
      setAuthLoading(false)
    }
  }

  const onResearch = async (values) => {
    setResearchLoading(true)
    try {
      const res = await apiRequest('/research', {
        method: 'POST',
        token,
        body: {
          query: values.query,
          preferences: {
            tone: values.tone,
            creativity: values.creativity,
            audience: values.audience,
            depth: values.depth,
            output_format: values.output_format,
            language: values.language,
            max_sources: values.max_sources,
            extra_context: values.extra_context,
            include_citations: values.include_citations,
          },
        },
      })
      setResearchResult(res)
      setCredits(res.credits_remaining ?? credits)
      msg.success('Research complete')
      await loadDashboard(token)
    } catch (error) {
      msg.error(error.message)
    } finally {
      setResearchLoading(false)
    }
  }

  const onProfile = async (values) => {
    setAccountLoading(true)
    try {
      const res = await apiRequest('/auth/me', {
        method: 'PATCH',
        token,
        body: { name: values.name },
      })
      setUser((current) => ({ ...current, ...res }))
      msg.success('Profile updated')
      await loadDashboard(token)
    } catch (error) {
      msg.error(error.message)
    } finally {
      setAccountLoading(false)
    }
  }

  const onPassword = async (values) => {
    setAccountLoading(true)
    try {
      const res = await apiRequest('/auth/change-password', {
        method: 'POST',
        token,
        body: values,
      })
      setToken(res.access_token)
      setTokenState(res.access_token)
      passwordForm.resetFields()
      msg.success('Password changed')
      await loadDashboard(res.access_token)
    } catch (error) {
      msg.error(error.message)
    } finally {
      setAccountLoading(false)
    }
  }

  const onSubscribe = async (planCode) => {
    setSubLoading(planCode)
    try {
      const res = await apiRequest('/billing/subscriptions', {
        method: 'POST',
        token,
        body: { plan_code: planCode, customer_email: user?.email },
      })
      const Razorpay = await loadRazorpay()
      const checkout = {
        ...(res.checkout || {}),
        key: res.key_id || res.checkout?.key,
        subscription_id: res.razorpay_subscription_id || res.checkout?.subscription_id,
        handler: async () => {
          msg.success('Payment processed')
          await loadDashboard(token)
        },
      }
      const rzp = new Razorpay(checkout)
      rzp.on('payment.failed', () => msg.error('Payment failed'))
      rzp.open()
    } catch (error) {
      msg.error(error.message)
    } finally {
      setSubLoading('')
    }
  }

  const onDisable = async () => {
    try {
      await apiRequest('/account/disable', { method: 'POST', token })
      msg.success('Account disabled')
      logout()
    } catch (error) {
      msg.error(error.message)
    }
  }

  const logout = () => {
    clearToken()
    setTokenState(null)
    setUser(null)
    setOverview(null)
    setCredits(0)
    setSessions([])
    setTransactions([])
    setSubscriptions([])
    setFiles([])
    setBilling(null)
    setResearchResult(null)
    authForm.resetFields()
    researchForm.resetFields()
    profileForm.resetFields()
    passwordForm.resetFields()
    setTab('research')
  }

  const authScreen = (
    <Layout className="app-shell">
      <Content className="mx-auto flex w-full max-w-7xl items-center px-4 py-8">
        <div className="grid w-full gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="glass-card rounded-3xl border border-white/40 p-8 shadow-soft">
            <Tag color="cyan" className="!mb-4 !rounded-full">
              Lumoura
            </Tag>
            <Typography.Title level={1} className="!mb-3 !mt-0 display-font">
              Clean research dashboard
            </Typography.Title>
            <Typography.Paragraph className="!mb-0 !max-w-2xl !text-base !text-slate-600">
              Research, credits, subscriptions, files, and account history are all in one simple UI
              built for your deployed backend.
            </Typography.Paragraph>
            <Divider />
            <Row gutter={16}>
              <Col xs={24} md={8}><StatCard title="Backend" value="Live" icon={<CheckCircleFilled />} /></Col>
              <Col xs={24} md={8}><StatCard title="Auth" value="JWT" icon={<SafetyOutlined />} /></Col>
              <Col xs={24} md={8}><StatCard title="Storage" value="Mongo + Cloudinary" icon={<DownloadOutlined />} /></Col>
            </Row>
          </div>
          <Card className="glass-card border-0 shadow-soft">
            <div className="mb-5">
              <Typography.Title level={2} className="!mb-1 !mt-0 display-font">
                {authMode === 'login' ? 'Sign in' : 'Create account'}
              </Typography.Title>
              <div className="text-slate-500">Backend: {API_BASE_URL}</div>
            </div>
            <Form form={authForm} layout="vertical" onFinish={onAuth} requiredMark={false}>
              {authMode === 'register' && (
                <Form.Item name="name" label="Name" rules={[{ required: true }]}>
                  <Input size="large" prefix={<UserOutlined />} />
                </Form.Item>
              )}
              <Form.Item name="email" label="Email" rules={[{ required: true, type: 'email' }]}>
                <Input size="large" />
              </Form.Item>
              <Form.Item name="password" label="Password" rules={[{ required: true }]}>
                <Input.Password size="large" />
              </Form.Item>
              <Button type="primary" htmlType="submit" size="large" block loading={authLoading}>
                {authMode === 'login' ? 'Sign in' : 'Create account'}
              </Button>
              <Button
                type="link"
                block
                className="!mt-2"
                onClick={() => setAuthMode((v) => (v === 'login' ? 'register' : 'login'))}
              >
                {authMode === 'login' ? 'Need an account?' : 'Already have an account?'}
              </Button>
            </Form>
          </Card>
        </div>
      </Content>
    </Layout>
  )

  const dashboard = (
    <Layout className="app-shell">
      <Header className="!h-auto !bg-transparent !p-0">
        <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-4 py-5">
          <div>
            <div className="section-label">Lumoura</div>
            <Typography.Title level={3} className="!mb-0 !mt-1 display-font">
              Research dashboard
            </Typography.Title>
          </div>
          <Space wrap>
            <Button icon={<ReloadOutlined />} onClick={() => loadDashboard(token)} loading={dashboardLoading}>
              Refresh
            </Button>
            <Button icon={<LogoutOutlined />} danger onClick={logout}>
              Sign out
            </Button>
          </Space>
        </div>
      </Header>

      <Content className="mx-auto w-full max-w-7xl px-4 pb-10">
        <Card className="glass-card mb-6 border-0 shadow-soft">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <div className="section-label">Signed in as</div>
              <Typography.Title level={2} className="!mb-1 !mt-1 display-font">
                {user?.name}
              </Typography.Title>
              <div className="text-slate-600">{user?.email}</div>
            </div>
            <div className="flex flex-wrap gap-2">
              <Tag color="blue">User ID: {shortId(user?.user_id)}</Tag>
              <Tag color="purple">Credits: {credits}</Tag>
              <Tag color={user?.plan_status === 'active' ? 'green' : 'gold'}>
                {user?.plan_status || 'free'}
              </Tag>
            </div>
          </div>
          <Divider />
          <Row gutter={[16, 16]}>
              <Col xs={12} md={8} xl={4}><StatCard title="Credits" value={credits} icon={<WalletOutlined />} /></Col>
              <Col xs={12} md={8} xl={4}><StatCard title="Research" value={overview?.research_sessions ?? sessions.length} icon={<RocketOutlined />} /></Col>
              <Col xs={12} md={8} xl={4}><StatCard title="Transactions" value={overview?.transactions ?? transactions.length} icon={<CheckCircleFilled />} /></Col>
              <Col xs={12} md={8} xl={4}><StatCard title="Files" value={overview?.files ?? files.length} icon={<DownloadOutlined />} /></Col>
              <Col xs={12} md={8} xl={4}><StatCard title="Subs" value={overview?.subscriptions ?? subscriptions.length} icon={<SafetyOutlined />} /></Col>
            </Row>
          </Card>

        <Tabs
          activeKey={tab}
          onChange={setTab}
          items={[
            {
              key: 'research',
              label: 'Research',
              children: (
                <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
                  <Card className="glass-card border-0 shadow-soft" title="Run research">
                    <Form form={researchForm} layout="vertical" initialValues={initialPrefs} onFinish={onResearch}>
                      <Form.Item name="query" label="Query" rules={[{ required: true }]}>
                        <TextArea rows={4} maxLength={500} showCount placeholder="What should we research?" />
                      </Form.Item>
                      <Row gutter={16}>
                        <Col xs={24} md={12}>
                          <Form.Item name="tone" label="Tone">
                            <Select options={toneOptions.map((v) => ({ value: v, label: v }))} />
                          </Form.Item>
                        </Col>
                        <Col xs={24} md={12}>
                          <Form.Item name="audience" label="Audience">
                            <Select options={audienceOptions.map((v) => ({ value: v, label: v }))} />
                          </Form.Item>
                        </Col>
                      </Row>
                      <Row gutter={16}>
                        <Col xs={24} md={12}>
                          <Form.Item name="depth" label="Depth">
                            <Select options={depthOptions} />
                          </Form.Item>
                        </Col>
                        <Col xs={24} md={12}>
                          <Form.Item name="output_format" label="Output format">
                            <Select options={formatOptions.map((v) => ({ value: v, label: v }))} />
                          </Form.Item>
                        </Col>
                      </Row>
                      <Row gutter={16}>
                        <Col xs={24} md={12}>
                          <Form.Item name="language" label="Language"><Input /></Form.Item>
                        </Col>
                        <Col xs={24} md={12}>
                          <Form.Item name="creativity" label="Creativity"><Slider min={0} max={10} /></Form.Item>
                        </Col>
                      </Row>
                      <Row gutter={16}>
                        <Col xs={24} md={12}>
                          <Form.Item name="max_sources" label="Max sources"><InputNumber min={1} max={10} className="!w-full" /></Form.Item>
                        </Col>
                        <Col xs={24} md={12}>
                          <Form.Item name="include_citations" label="Include citations" valuePropName="checked"><Switch /></Form.Item>
                        </Col>
                      </Row>
                      <Form.Item name="extra_context" label="Extra context"><TextArea rows={3} /></Form.Item>
                      <Button type="primary" htmlType="submit" icon={<SendOutlined />} loading={researchLoading}>
                        Run research
                      </Button>
                    </Form>
                  </Card>

                  <Card className="glass-card border-0 shadow-soft" title="Latest result">
                    {researchLoading ? (
                      <Skeleton active paragraph={{ rows: 8 }} />
                    ) : researchResult ? (
                      <div className="space-y-4">
                        <div className="flex flex-wrap gap-2">
                          <Tag color="cyan">{researchResult.preferences?.tone || 'default'}</Tag>
                          <Tag color="blue">{researchResult.preferences?.depth || 'balanced'}</Tag>
                          <Tag color="geekblue">{researchResult.sources_used || 0} sources</Tag>
                          <Tag color="purple">{researchResult.credits_remaining ?? '—'} credits left</Tag>
                        </div>
                        <Alert message={researchResult.query} description={researchResult.answer} type="info" showIcon />
                        {researchResult.export?.cloudinary_url && (
                          <Button type="link" href={researchResult.export.cloudinary_url} target="_blank" rel="noreferrer" className="!px-0">
                            Open saved export
                          </Button>
                        )}
                        <Divider className="!my-2" />
                        {researchResult.sources?.length ? (
                          <List
                            dataSource={researchResult.sources}
                            renderItem={(source, idx) => (
                              <List.Item key={source.url || idx}>
                                <Card size="small" className="w-full bg-slate-50/80">
                                  <div className="font-medium">{source.title || `Source ${idx + 1}`}</div>
                                  <div className="mt-1 text-sm text-slate-600">{source.snippet || source.content || 'No snippet available'}</div>
                                  {source.url && <a className="mt-2 inline-block text-sm text-cyan-700 hover:underline" href={source.url} target="_blank" rel="noreferrer">{source.url}</a>}
                                </Card>
                              </List.Item>
                            )}
                          />
                        ) : (
                          <EmptyState title="No sources" description="The run returned no source records." />
                        )}
                      </div>
                    ) : (
                      <EmptyState title="Nothing yet" description="Run a research query to see the answer here." />
                    )}
                  </Card>
                </div>
              ),
            },
            {
              key: 'history',
              label: 'History',
              children: (
                <div className="grid gap-6 xl:grid-cols-3">
                  <Card className="glass-card border-0 shadow-soft xl:col-span-2" title="Research sessions">
                    {sessions.length ? (
                      <List
                        dataSource={sessions}
                        renderItem={(session) => (
                          <List.Item actions={session.export?.cloudinary_url ? [<Button key="e" type="link" href={session.export.cloudinary_url} target="_blank" rel="noreferrer">Export</Button>] : []}>
                            <List.Item.Meta
                              title={<Space wrap><span>{session.query}</span><Tag color={session.status === 'complete' ? 'green' : 'gold'}>{session.status}</Tag></Space>}
                              description={<div className="space-y-1 text-sm text-slate-600"><div>{session.answer ? session.answer.slice(0, 200) : 'No answer yet'}</div><div>Created: {fmtDate(session.created_at)} · Credits: {session.credits_cost}</div></div>}
                            />
                          </List.Item>
                        )}
                      />
                    ) : (
                      <EmptyState title="No sessions yet" description="Completed research runs will show up here." />
                    )}
                  </Card>

                  <Card className="glass-card border-0 shadow-soft" title="Files">
                    {files.length ? (
                      <List
                        dataSource={files}
                        renderItem={(file) => (
                          <List.Item actions={file.cloudinary_url ? [<Button key="o" type="link" href={file.cloudinary_url} target="_blank" rel="noreferrer">Open</Button>] : []}>
                            <List.Item.Meta
                              title={file.filename || 'Export'}
                              description={<div className="text-sm text-slate-600">{fmtDate(file.created_at)}</div>}
                            />
                          </List.Item>
                        )}
                      />
                    ) : <EmptyState title="No files" description="Saved exports appear here." />}
                  </Card>

                  <Card className="glass-card border-0 shadow-soft xl:col-span-3" title="Transactions">
                    {transactions.length ? (
                      <Row gutter={[16, 16]}>
                        {transactions.map((tx) => (
                          <Col xs={24} md={12} key={tx.id}>
                            <Card size="small" className="bg-slate-50/80">
                              <div className="flex items-center justify-between gap-2">
                                <Tag color={tx.type === 'debit' ? 'red' : 'green'}>{tx.type}</Tag>
                                <span className="text-xs text-slate-500">{fmtDate(tx.created_at)}</span>
                              </div>
                              <div className="mt-2 font-medium">{tx.reason || 'credit movement'}</div>
                              <div className="mt-1 text-sm text-slate-600">Amount: {tx.amount}</div>
                            </Card>
                          </Col>
                        ))}
                      </Row>
                    ) : <EmptyState title="No transactions" description="Credit movement will show here." />}
                  </Card>
                </div>
              ),
            },
            {
              key: 'billing',
              label: 'Billing',
              children: (
                <div className="grid gap-6 xl:grid-cols-2">
                  <Card className="glass-card border-0 shadow-soft" title="Plans">
                    {billing?.plans?.length ? billing.plans.map((plan) => (
                      <Card key={plan.code} size="small" className="mb-3 bg-slate-50/80 last:mb-0">
                        <div className="flex items-center justify-between gap-3">
                          <div>
                            <div className="font-semibold">{plan.name} <Tag color="blue">{plan.code}</Tag></div>
                            <div className="mt-1 text-sm text-slate-600">{plan.credits_per_cycle} credits every {plan.interval} {plan.period}</div>
                            <div className="mt-1 text-sm text-slate-600">Amount: {(plan.amount / 100).toFixed(2)} {plan.currency}</div>
                          </div>
                          <Button type="primary" loading={subLoading === plan.code} onClick={() => onSubscribe(plan.code)}>
                            Subscribe
                          </Button>
                        </div>
                      </Card>
                    )) : <Spin />}
                  </Card>

                  <Card className="glass-card border-0 shadow-soft" title="Subscriptions">
                    {subscriptions.length ? (
                      <List
                        dataSource={subscriptions}
                        renderItem={(sub) => (
                          <List.Item>
                            <List.Item.Meta
                              title={<Space wrap><span>{sub.plan_code}</span><Tag color={sub.status === 'active' ? 'green' : 'gold'}>{sub.status}</Tag></Space>}
                              description={<div className="text-sm text-slate-600">Credits: {sub.credits_per_cycle} · Charge at: {fmtDate(sub.charge_at)} · ID: {shortId(sub.razorpay_subscription_id)}</div>}
                            />
                          </List.Item>
                        )}
                      />
                    ) : <EmptyState title="No subscriptions" description="Subscribe to top up credits automatically." />}
                  </Card>
                </div>
              ),
            },
            {
              key: 'account',
              label: 'Account',
              children: (
                <div className="grid gap-6 xl:grid-cols-2">
                  <Card className="glass-card border-0 shadow-soft" title="Profile">
                    <Form form={profileForm} layout="vertical" initialValues={{ name: user?.name }} onFinish={onProfile}>
                      <Form.Item name="name" label="Display name" rules={[{ required: true }]}>
                        <Input prefix={<UserOutlined />} />
                      </Form.Item>
                      <Button type="primary" htmlType="submit" loading={accountLoading}>Update profile</Button>
                    </Form>
                    <Divider />
                    <div className="space-y-2 text-sm text-slate-600">
                      <div>Email: {user?.email || '—'}</div>
                      <div>User ID: {user?.user_id || '—'}</div>
                      <div>Updated: {fmtDate(user?.updated_at)}</div>
                    </div>
                  </Card>

                  <Card className="glass-card border-0 shadow-soft" title="Security">
                    <Form form={passwordForm} layout="vertical" onFinish={onPassword}>
                      <Form.Item name="current_password" label="Current password" rules={[{ required: true }]}>
                        <Input.Password />
                      </Form.Item>
                      <Form.Item name="new_password" label="New password" rules={[{ required: true }]}>
                        <Input.Password />
                      </Form.Item>
                      <Button type="primary" htmlType="submit" loading={accountLoading}>Change password</Button>
                    </Form>
                    <Divider />
                    <Popconfirm title="Disable this account?" onConfirm={onDisable} okText="Disable" okButtonProps={{ danger: true }}>
                      <Button danger icon={<DeleteOutlined />}>Disable account</Button>
                    </Popconfirm>
                  </Card>
                </div>
              ),
            },
          ]}
        />
      </Content>
    </Layout>
  )

  return (
    <ConfigProvider
      theme={{
        token: { colorPrimary: '#0f766e', borderRadius: 14, fontFamily: 'Inter, sans-serif' },
        components: { Card: { headerBg: 'rgba(255,255,255,0.7)' } },
      }}
    >
      <AntApp>
        {holder}
        {booting ? (
          <div className="flex min-h-screen items-center justify-center"><Spin size="large" /></div>
        ) : token && user ? dashboard : authScreen}
      </AntApp>
    </ConfigProvider>
  )
}
