-- World-space planted targets, rendered by native hierarchical bone manipulators.
local function add(a,b) return {a[1]+b[1],a[2]+b[2],a[3]+b[3]} end
local function sub(a,b) return {a[1]-b[1],a[2]-b[2],a[3]-b[3]} end
local function mul(a,s) return {a[1]*s,a[2]*s,a[3]*s} end
local function dot(a,b) return a[1]*b[1]+a[2]*b[2]+a[3]*b[3] end
local function cross(a,b) return {a[2]*b[3]-a[3]*b[2],a[3]*b[1]-a[1]*b[3],a[1]*b[2]-a[2]*b[1]} end
local function length(a) return math.sqrt(dot(a,a)) end
local function norm(a) return mul(a,1/math.max(0.000001,length(a))) end
local function clamp(x,a,b) return math.max(a,math.min(b,x)) end
local function smooth(t) return t*t*t*(10+t*(-15+6*t)) end
local function qmul(a,b)
 return {a[4]*b[1]+a[1]*b[4]+a[2]*b[3]-a[3]*b[2],a[4]*b[2]-a[1]*b[3]+a[2]*b[4]+a[3]*b[1],a[4]*b[3]+a[1]*b[2]-a[2]*b[1]+a[3]*b[4],a[4]*b[4]-a[1]*b[1]-a[2]*b[2]-a[3]*b[3]}
end
local function rotate(q,v)
 local t=mul(cross({q[1],q[2],q[3]},v),2)
 return add(v,add(mul(t,q[4]),cross({q[1],q[2],q[3]},t)))
end
local function arc(a,b)
 a=norm(a);b=norm(b);local v=cross(a,b);local w=1+dot(a,b)
 if w<0.00001 then v=norm(cross(a,{0,1,0}));w=0 end
 local l=math.sqrt(dot(v,v)+w*w)
 return {v[1]/l,v[2]/l,v[3]/l,w/l}
end
local function qblend(a,b,t)
 local s=a[1]*b[1]+a[2]*b[2]+a[3]*b[3]+a[4]*b[4]<0 and -1 or 1
 local q={};local l=0
 for j=1,4 do q[j]=a[j]*(1-t)+b[j]*t*s;l=l+q[j]*q[j] end
 for j=1,4 do q[j]=q[j]/math.sqrt(l) end
 return q
end
local function horizontalOrientation(unit)
 local q=unit:GetOrientation();local f=rotate(q,{0,0,1});local h=math.atan2(f[1],f[3])
 return {0,math.sin(h/2),0,math.cos(h/2)}
end
local function ground(p,height)
 return {p[1],GetTerrainHeight(p[1],p[3])+height,p[3]}
end

-- Solve the original two link lengths without moving the planted ankle.
function Solve(hip,ankle,pole,l1,l2)
 local delta=sub(ankle,hip);local distance=length(delta);local dir=norm(delta)
 local d=clamp(distance,math.abs(l1-l2)+.00001,l1+l2-.00001)
 local a=(l1*l1-l2*l2+d*d)/(2*d)
 local perpendicular=norm(sub(pole,mul(dir,dot(pole,dir))))
 local knee=add(hip,add(mul(dir,a),mul(perpendicular,math.sqrt(math.max(0,l1*l1-a*a)))))
 return knee,math.max(0,distance-(l1+l2))
end

function Initialize(unit)
 local spec=import('/mods/Project Roc Unicorns/lua/razlom_leg_data.lua').Legs
 local q=horizontalOrientation(unit);local origin=unit:GetPosition()
 unit.Gait={legs={},rig={},last={origin[1],origin[2],origin[3]},lastQ=q,time=0,nextGroup=1,active=false,cooldown=0}
 for _,d in ipairs(spec) do
  local desired={d.ankle[1],d.ankle[2],d.ankle[3]}
  -- A slightly flexed stance leaves reach for planted steps in either direction.
  desired[1]=d.hip[1]+(desired[1]-d.hip[1])*.73
  desired[3]=d.hip[3]+(desired[3]-d.hip[3])*.73
  local leg={data=d,ideal=desired,foot=ground(add(origin,rotate(q,desired)),d.ankle[2]),orientation=q}
  table.insert(unit.Gait.legs,leg)
 end
 unit.Gait.body=CreateSlider(unit,0)
 unit.Gait.body:SetWorldUnits(true)
 unit.Gait.body:SetGoal(0,0,0)
 unit.Gait.body:SetSpeed(.5)
 unit.Trash:Add(unit.Gait.body)
 Update(unit,0)
 unit:ForkThread(function(u)
  while not u.Dead and not u:BeenDestroyed() do
   WaitTicks(1)
   if not u.Dead then Update(u,.1) end
  end
 end)
end

local function inverse(q) return {-q[1],-q[2],-q[3],q[4]} end
local function euler(q)
 local x,y,z,w=q[1],q[2],q[3],q[4]
 return {math.atan2(2*(w*x+y*z),1-2*(x*x+y*y))*180/math.pi,
 math.asin(clamp(2*(w*y-z*x),-1,1))*180/math.pi,
 math.atan2(2*(w*z+x*y),1-2*(y*y+z*z))*180/math.pi}
end
local function poseBone(unit,bone,orientation,dt)
 local g=unit.Gait;local rig=g.rig[bone];local angles=euler(orientation)
 if not rig then
  rig={};g.rig[bone]=rig
  for i,axis in ipairs({'x','y','z'}) do
   local m=CreateRotator(unit,bone,axis,0,0,0,0)
   m:SetPrecedence(40-i)
   unit.Trash:Add(m);rig[i]=m
  end
 end
 for i=1,3 do
  local m=rig[i];local current=m:GetCurrentAngle()
  -- FA uses Lua 5.0: arithmetic modulo syntax is unsupported.
  local delta=angles[i]-current
  local difference=delta-360*math.floor((delta+180)/360)
  local target=current+difference
  if dt==0 then m:SetCurrentAngle(target) else
   m:SetSpeed(math.max(.01,math.abs(difference)/dt))
   m:SetGoal(target)
  end
 end
end
local function impact(unit,leg)
 local parts=unit.LegVisuals[leg.data.name..'_Clawed_foot']
 local foot=parts and parts[1]
 if foot and not foot:BeenDestroyed() then
  for _,fx in ipairs(import('/lua/effecttemplates.lua').FootFall01) do
   CreateEmitterAtEntity(foot,unit.Army,fx):OffsetEmitter(0,-leg.data.ankle[2],0):ScaleEmitter(1.4)
  end
 end
 -- Called exactly once, after the visible foot has reached its planted pose.
 unit:PlayUnitSound('FootFallGeneric')
 unit:ShakeCamera(22,.09,0,.10)
 unit.Gait.landings=(unit.Gait.landings or 0)+1
end

function Update(unit,dt)
 local g=unit.Gait;if not g then return end
 g.time=g.time+dt
 -- A previous target pose has now had one native tick to interpolate to contact.
 for _,leg in ipairs(g.legs) do
  if leg.contactPending then leg.contactPending=false;impact(unit,leg) end
 end
 local op=unit:GetPosition();local origin={op[1],op[2],op[3]};local q=horizontalOrientation(unit)
 local forward=rotate(q,{0,0,1});local oldForward=rotate(g.lastQ,{0,0,1})
 local angular=dt>0 and math.atan2(cross(oldForward,forward)[2],dot(oldForward,forward))/dt or 0
 local anticipated=qmul({0,math.sin(angular*.4/2),0,math.cos(angular*.4/2)},q)
 local velocity=dt>0 and mul(sub(origin,g.last),1/dt) or {0,0,0};velocity[2]=0
 if length(velocity)>5 then velocity={0,0,0} end -- teleport does not create an enormous step
 local moving=length(velocity)>.02 or unit.Moving
 g.cooldown=math.max(0,g.cooldown-dt)
 local active=false
 for _,leg in ipairs(g.legs) do
  if leg.swing then
   leg.elapsed=leg.elapsed+dt
   local t=clamp(leg.elapsed/leg.duration,0,1);local s=smooth(t)
   leg.foot=add(mul(leg.start,1-s),mul(leg.finish,s))
   leg.foot[2]=leg.foot[2]+.55*math.sin(math.pi*t)^2
   leg.orientation=qblend(leg.startQ,leg.finishQ,s)
   if t>=1 then leg.foot=leg.finish;leg.orientation=leg.finishQ;leg.swing=false;leg.landed=true else active=true end
  end
 end
 if not active and moving and g.cooldown<=0 then
  local worst=0
  for _,leg in ipairs(g.legs) do
   local ideal=ground(add(origin,rotate(q,leg.ideal)),leg.data.ankle[2])
   local e=sub(ideal,leg.foot);e[2]=0;worst=math.max(worst,length(e))
  end
  if worst>.16 then
   local rank=0
   for _,leg in ipairs(g.legs) do
    if leg.data.group==g.nextGroup then
     rank=rank+1
     leg.swing=true;leg.elapsed=0;leg.duration=.2+rank*.1
     leg.start={leg.foot[1],leg.foot[2],leg.foot[3]};leg.startQ=leg.orientation;leg.finishQ=anticipated
     leg.finish=ground(add(add(origin,rotate(anticipated,leg.ideal)),mul(velocity,leg.duration)),leg.data.ankle[2])
    end
   end
   g.nextGroup=3-g.nextGroup
  end
 end
 -- Transfer a little weight towards the support triangle, settling as feet land.
 local supportX=0;local lift=0;local support=0
 for _,leg in ipairs(g.legs) do
  if leg.swing then lift=lift+math.sin(math.pi*clamp(leg.elapsed/leg.duration,0,1))^2
  else supportX=supportX+leg.ideal[1];support=support+1 end
 end
 g.body:SetGoal(clamp(supportX/math.max(1,support)*.035,-.06,.06),-.045*lift/3,0)
 for _,leg in ipairs(g.legs) do
  local d=leg.data
  -- Native bone origin includes the actual interpolated body slider position.
  local hp=unit:GetPosition(d.name..'_Hip_link');local hip={hp[1],hp[2],hp[3]}
  local upper=sub(d.knee,d.hip);local lower=sub(d.ankle,d.knee)
  local knee,error=Solve(hip,leg.foot,rotate(q,d.pole),length(upper),length(lower))
  g.maxReachError=math.max(g.maxReachError or 0,error)
  local hq=qmul(arc(rotate(q,upper),sub(knee,hip)),q)
  local kq=qmul(arc(rotate(q,lower),sub(leg.foot,knee)),q)
  poseBone(unit,d.name..'_Hip_link',qmul(inverse(q),hq),dt)
  poseBone(unit,d.name..'_Armored_shin',qmul(inverse(hq),kq),dt)
  poseBone(unit,d.name..'_Clawed_foot',qmul(inverse(kq),leg.orientation),dt)
  if leg.landed then leg.landed=false;leg.contactPending=true end
 end
 g.last={origin[1],origin[2],origin[3]}
 g.lastQ=q
end
