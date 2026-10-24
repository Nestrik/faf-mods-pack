import fs from 'node:fs/promises';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
const require=createRequire('C:/Users/Nestr/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/package.json');
const {Workbook,SpreadsheetFile,FileBlob}=await import(pathToFileURL(require.resolve('@oai/artifact-tool')).href);
const dir='D:/Games/FafModsCreate/outputs/experimental_units_20261024';
if(process.argv.includes('--filters-only')){
  const filename=`${dir}/Экспериментальные_юниты_Seraphim_Rework_и_BlackOpsFAF.xlsx`;
  const existing=await SpreadsheetFile.importXlsx(await FileBlob.load(filename));
  for(let i=0;i<8;i++)for(const t of existing.worksheets.getItemAt(i).tables.items)t.showFilterButton=true;
  existing.recalculate();
  const preview=await existing.render({sheetName:'Сравнение',range:'A2:O13',scale:1.25,format:'png'});
  await fs.writeFile(`${dir}/work/preview_1.png`,new Uint8Array(await preview.arrayBuffer()));
  const output=await SpreadsheetFile.exportXlsx(existing);await output.save(filename);
  console.log('Enabled filter buttons on all 9 tables');
  process.exit(0);
}
const data=JSON.parse(await fs.readFile(`${dir}/work/data.json`,'utf8'));
const wb=Workbook.create();
const units=data.units;
const sheets={};
const sources=[...new Set([...data.raw.map(x=>x[7]),...data.scripts.map(x=>x[5])])];
const sourceMap=new Map(sources.map((p,i)=>[p,`S${String(i+1).padStart(3,'0')}`]));
const clean=s=>typeof s==='string'?s.replace(/<LOC [^>]+>/g,''):s;
const val=(o,p)=>{for(const k of p.split('.')) o=o?.[k]; return o??null;};
const arr=x=>Array.isArray(x)?x:[];
const show=x=>x===undefined||x===null?null:typeof x==='object'?JSON.stringify(x):typeof x==='boolean'?(x?'Да':'Нет'):clean(x);
const g=(u,p)=>show(val(u.bp,p));
const fac={Seraphim:'Серафим',UEF:'ОФЗ',Aeon:'Эон',Cybran:'Кибран'};
const mod=u=>u.mod==='seraphim-rework'?'Seraphim Rework':u.mod.replace('BlackOpsFAF-','BO: ');
const fixed=u=>[u.id,u.name,fac[u.faction]??u.faction,mod(u)];
const fields=(u,ps)=>ps.map(p=>g(u,p));
function col(n){let s='';for(n++;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;}
function table(name,title,subtitle,headers,rows,widths={},freeze=2){
  const s=wb.worksheets.add(name); sheets[name]=s; s.showGridLines=false;
  const last=col(headers.length-1),end=rows.length+5;
  s.getRange(`A1:${last}${end}`).format.font={name:'Arial',size:10,color:'#202936'};
  s.getRange(`A1:${last}${end}`).format.verticalAlignment='center';
  s.getRange(`A2`).values=[[title]];s.getRange('A2').format.font={name:'Arial',size:15,bold:true,color:'#203853'};
  s.getRange(`A3`).values=[[subtitle]];s.getRange('A3').format.font={name:'Arial',size:10,italic:true,color:'#596576'};
  s.getRange(`A5:${last}${end}`).values=[headers,...rows.map(r=>r.map(x=>typeof x==='string'&&x.startsWith('=')?"'"+x:x??null))];
  s.tables.add(`A5:${last}${end}`,true,`Table${Object.keys(sheets).length}`).showFilterButton=true;
  s.getRange(`A5:${last}5`).format={fill:'#243F5B',font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},wrapText:true,horizontalAlignment:'center',verticalAlignment:'center',rowHeight:44};
  if(rows.length){
    const body=s.getRange(`A6:${last}${end}`);body.format.rowHeight=27;body.format.numberFormat='General';
    body.format.horizontalAlignment='left';
    for(let c=0;c<headers.length;c++){
      const xs=rows.map(r=>r[c]).filter(x=>x!==null&&x!==undefined);
      if(xs.length&&xs.every(x=>typeof x==='number')){
        const cr=s.getRange(`${col(c)}6:${col(c)}${end}`);
        const digits=Math.min(5,Math.max(...xs.map(x=>Number.isInteger(x)?0:(String(x).split('.')[1]??'').length)));
        cr.format.horizontalAlignment='right';cr.format.numberFormat=digits?'#,##0.'+'0'.repeat(digits):'#,##0';
      }
    }
  }
  for(let c=0;c<headers.length;c++)s.getRange(`${col(c)}5:${col(c)}${end}`).format.columnWidth=widths[c]??16;
  s.freezePanes.freezeRows(5);if(freeze)s.freezePanes.freezeColumns(freeze);
  console.log(`Prepared ${name}: ${rows.length} rows`);
  return s;
}
const type=u=>{
  const c=u.bp.Categories??[];
  if(u.helper)return 'Служебный объект';
  if(c.includes('SATELLITE'))return 'Спутник';
  if(c.includes('STRUCTURE'))return 'Постройка';
  if(c.includes('AIR'))return 'Авиация';
  if(c.includes('NAVAL'))return 'Флот';
  return c.includes('HOVER')?'Наземный ховер':'Наземный юнит';
};
const special={
 GGA0401:'Личный щит. Основное орудие с зарядкой. Боевые параметры см. также в скрипте.',
 GGA0402:'Личный щит. Два фазонных ствола. Отдельный скрипт оружия и снаряда.',
 GGA0403:'Личный щит. Отдельный вариант корпуса и основной пушки.',
 GGA1401:'При гибели полностью построенного генератора вызывается штатный Othuy. Щит переключается отдельно от производства.',
 EEA0002:'Создаётся улучшением SpySat командира ОФЗ. Цена в чертеже спутника номинальная. Улучшение: 2250 массы, 270000 энергии, 8100 работы, требуется ElectronicsEnhancment.',
 BAA0401:'В описании экспериментальный спутник, в категориях TECH1. Строится только центром Artemis.',
 BAB2404:'Центр управления оплачивается отдельно от спутника Artemis. BuildRate центра = 1080.',
 BSB0405:'Скрипт уменьшает входящий урон до ceil(урон × 0.3). Лямбда-поле: радиус 21, Probability=20 (21/101). Поле зависит от переключателя и запаса энергии.',
 BSL0401:'Танк с боевыми дронами. Их параметры не суммированы с оружием самого танка.',
 BSS0401:'Специальные боеприпасы вызывают энергетические сущности Othuy. Их чертежи выделены как служебные.',
 BSB2402:'Квантовая арка и дочерние фабрики. Производимые подкрепления не включены в состав самой арки.',
 EEB0402:'Базовые параметры без StellarBuff. StellarBuff удваивает массу, энергия = базовая × 2 − 1. Стоимость строительства не меняет.',
 BSB0002:'Служебная дочерняя фабрика квантовой арки. Не является отдельной строительной позицией.',
 BSL0403:'Служебная энергетическая сущность. Стоимость в чертеже номинальная, отдельно не строится.',
 BSL0404:'Служебная энергетическая сущность. Стоимость в чертеже номинальная, отдельно не строится.'
};

const baseHeaders=['ID','Название','Фракция','Мод'];
const sumRows=units.map(u=>{
  const weapons=arr(u.bp.Weapon),combat=weapons.filter(w=>!(/death|collossusdeath/i.test(w.Label??'')||w.WeaponCategory==='Death'));
  const ranges=combat.map(w=>w.MaxRadius).filter(x=>typeof x==='number');
  return [...fixed(u),type(u),u.helper?'Служебный':'Основной',g(u,'Economy.BuildCostMass'),g(u,'Economy.BuildCostEnergy'),g(u,'Economy.BuildTime'),g(u,'Defense.MaxHealth'),g(u,'Defense.Shield.ShieldMaxHealth'),g(u,'Physics.MaxSpeed'),ranges.length?Math.max(...ranges):null,weapons.length,sourceMap.get(u.path)];
});
const summary=table('Сравнение','Экспериментальные юниты FAF','Seraphim Rework и BlackOpsFAF • 21 основной юнит + 3 служебных объекта • снимок локальных файлов: 24.10.2026',
 [...baseHeaders,'Тип','Участие','Масса','Энергия','Работа, очки','Корпус, HP','Щит, HP','Скорость','Макс. дальность¹','Записей оружия','Источник'],sumRows,{0:14,1:27,2:13,3:22,4:24,5:14,6:13,7:16,8:16,9:16,10:14,11:14,12:19,13:18,14:13});
summary.tabColor='#243F5B';
summary.getRange('A32').values=[['¹ Максимальная явно указанная дальность оружия, кроме записей смерти. Учитывается также ПВО/ПРО. Пустая ячейка означает отсутствие поля, а не ноль.']];

const econPaths=['Economy.BuildCostMass','Economy.BuildCostEnergy','Economy.BuildTime','Economy.BuildRate','Economy.ProductionPerSecondMass','Economy.ProductionPerSecondEnergy','Economy.MaintenanceConsumptionPerSecondMass','Economy.MaintenanceConsumptionPerSecondEnergy','Economy.MassStorage','Economy.EnergyStorage','Economy.AdjacentStructureEnergyMod','Wreckage.MassMult','Wreckage.EnergyMult','Wreckage.ReclaimTimeMultiplier'];
table('Экономика','Стоимость и экономика','Базовые значения чертежей. Работа — BuildTime, не секунды. Действие StellarBuff и цена SpySat описаны в примечаниях.',
 [...baseHeaders,'Масса','Энергия','Работа, очки','Скорость строительства','Масса / с','Энергия / с','Расход массы / с','Расход энергии / с','Хранилище массы','Хранилище энергии','Соседство: энергия','Обломки: доля массы','Обломки: доля энергии','Время утилизации ×','Источник'],units.map(u=>[...fixed(u),...fields(u,econPaths),sourceMap.get(u.path)]),{0:14,1:27,2:13,3:22});

const defPaths=['Defense.Health','Defense.MaxHealth','Defense.RegenRate','Defense.ArmorType','Defense.Shield.ShieldMaxHealth','Defense.Shield.PersonalShield','Defense.Shield.ShieldSize','Defense.Shield.ShieldRegenRate','Defense.Shield.ShieldRegenStartTime','Defense.Shield.ShieldRechargeTime','Defense.Shield.ShieldEnergyDrainRechargeTime','Defense.Shield.RegenAssistMult','Defense.AirThreatLevel','Defense.SurfaceThreatLevel','Defense.SubThreatLevel','Defense.EconomyThreatLevel','VeteranMassMult','Veteran.Level1','Veteran.Level2','Veteran.Level3','Veteran.Level4','Veteran.Level5'];
table('Защита','Корпус, щит и ветеранство','Значения из Defense и Veteran. Сопротивление скрипта BSB0405 и лямбда-поле рассматриваются отдельно от обычного щита.',
 [...baseHeaders,'Начальное HP','Максимум HP','Регенерация HP / с','Тип брони','Щит HP','Личный щит','Размер щита','Реген щита / с','Задержка регена, с','Перезарядка щита, с','После потери энергии, с','RegenAssistMult','Угроза воздуху','Угроза поверхности','Угроза под водой','Экономическая угроза','VeteranMassMult','Ветеран 1','Ветеран 2','Ветеран 3','Ветеран 4','Ветеран 5','Источник'],units.map(u=>[...fixed(u),...fields(u,defPaths),sourceMap.get(u.path)]),{0:14,1:27,2:13,3:22,7:24});

const movePaths=['Physics.MotionType','Physics.MaxSpeed','Physics.MaxSpeedReverse','Physics.MaxAcceleration','Physics.MaxBrake','Physics.TurnRate','Physics.TurnRadius','Physics.WaterSpeedMultiplier','Physics.Elevation','Intel.VisionRadius','Intel.WaterVisionRadius','Intel.RadarRadius','Intel.SonarRadius','Intel.OmniRadius','Intel.RadarStealth','Intel.SonarStealth','Intel.Cloak','Intel.RadarStealthFieldRadius','Intel.CloakFieldRadius','Transport.TransportClass','SizeX','SizeY','SizeZ','Footprint.SizeX','Footprint.SizeZ'];
table('Движение и разведка','Движение, разведка и размеры','Дистанции и размеры — игровые единицы. Режимы движения и категории сохранены по исходным данным.',
 [...baseHeaders,'Режим движения','Скорость','Задний ход','Ускорение','Торможение','Поворот','Радиус поворота','Скорость в воде ×','Высота','Обзор','Подводный обзор','Радар','Сонар','Омни','Радарная скрытность','Сонарная скрытность','Маскировка','Поле радарной скрытности','Поле маскировки','Класс транспорта','Размер X','Размер Y','Размер Z','Фундамент X','Фундамент Z','Категории','Возможности','Источник'],units.map(u=>[...fixed(u),...fields(u,movePaths),arr(u.bp.Categories).join(', '),arr(u.bp.Display?.Abilities).map(clean).join(', '),sourceMap.get(u.path)]),{0:14,1:27,2:13,3:22,4:26,29:80,30:55});

const weaponFields=[['DisplayName','Название оружия'],['WeaponCategory','Категория'],['RangeCategory','Класс дальности'],['Damage','Урон'],['DamageType','Тип урона'],['DamageRadius','Радиус урона'],['RateOfFire','RateOfFire, 1/с'],['MinRadius','Мин. дальность'],['MaxRadius','Макс. дальность'],['MuzzleVelocity','Скорость вылета'],['MuzzleSalvoSize','Снарядов в залпе'],['MuzzleSalvoDelay','Интервал залпа, с'],['ProjectilesPerOnFire','Снарядов на событие'],['RackSalvoSize','RackSalvoSize'],['RackSalvoReloadTime','Перезарядка стойки, с'],['RackFireTogether','Стойки одновременно'],['MuzzleChargeDelay','Зарядка дула, с'],['RackSalvoChargeTime','Зарядка стойки, с'],['BeamLifetime','BeamLifetime, с'],['BeamCollisionDelay','BeamCollisionDelay, с'],['DoTPulses','Импульсы DoT'],['DoTTime','Длительность DoT, с'],['EnergyRequired','Энергия на выстрел'],['EnergyDrainPerSecond','Расход оружия / с'],['ProjectileLifetime','Жизнь снаряда, с'],['BallisticArc','Баллистика'],['FireTargetLayerCapsTable','Допустимые слои целей'],['TargetRestrictOnlyAllow','Только цели'],['TargetRestrictDisallow','Запрещённые цели'],['TargetPriorities','Приоритеты целей'],['DamageFriendly','Урон союзникам'],['CollideFriendly','Столкновение с союзниками'],['ProjectileId','Чертёж снаряда']];
const weaponRows=[];
for(const u of units)for(const [idx,w] of arr(u.bp.Weapon).entries())weaponRows.push([...fixed(u),idx+1,w.Label??null,...weaponFields.map(([p])=>show(val(w,p))),sourceMap.get(u.path)]);
const ws=table('Оружие','Все записи вооружения','136 записей, включая ПВО, ПРО, торпеды и оружие смерти. Универсальный DPS не рассчитан: итог зависит от залпов, лучей и скриптов.',
 [...baseHeaders,'№','Label',...weaponFields.map(x=>x[1]),'Источник'],weaponRows,{0:14,1:27,2:13,3:22,4:8,5:25,6:38,7:30,8:26,32:65,33:45,34:45,35:65,38:85});
ws.getRange(`G6:I${weaponRows.length+5}`).format.wrapText=true;
ws.getRange(`A6:AN${weaponRows.length+5}`).format.rowHeight=40;

const rawRows=data.raw.map(r=>[...r.slice(0,5),r[5],r[6],sourceMap.get(r[7])]);
table('Все поля','Все явно заданные поля чертежей','Полный развёрнутый набор параметров юнитов и 72 привязок чертежей снарядов. Индексы массивов начинаются с 1.',
 ['ID юнита','Название','Объект','ID / виртуальный путь','Поле Lua','Значение','Тип данных','Источник'],rawRows,{0:15,1:29,2:13,3:65,4:70,5:100,6:14,7:12});

const scriptRows=data.scripts.map(r=>[...r.slice(0,5),sourceMap.get(r[5])]);
table('Скрипты','Скрипты и динамическая механика','Исходные строки скриптов юнитов, снарядов и общих модулей. Фильтруйте по ID, типу и коду источника.',
 ['ID юнита','Название / модуль','Тип скрипта','Строка','Код Lua','Источник'],scriptRows,{0:15,1:34,2:30,3:10,4:150,5:12});

const notes=[
 ['Общее','Состав','21 основной юнит из прошлого запроса: 4 Seraphim Rework и 17 BlackOpsFAF. Ещё 3 служебных объекта вынесены в отдельную категорию в сравнении.'],
 ['Общее','База данных','Снимок локальных файлов на 24.10.2026. Seraphim Rework — рабочий проект, BlackOpsFAF — установленные копии.'],
 ['Общее','Пустые значения','Поле не задано в данном чертеже. Это не равнозначно нулю или отсутствию функции: возможны стандартные значения движка и наследование скрипта.'],
 ['Общее','Работа','BuildTime — очки строительства. Без ограничений ресурсов время = BuildTime / суммарная эффективная скорость строительства.'],
 ['Общее','Вооружение','Damage — исходное поле оружия. Не является DPS. RateOfFire не учитывает автоматически зарядку, стойки, залпы, задержки и специальные скрипты.'],
 ['Общее','Дальность','Максимальная дальность в сравнении берётся из MaxRadius всех записей оружия, кроме записей смерти. Поэтому значение может относиться к ПВО или ПРО.'],
 ['Общее','Полнота','Все явно заданные поля выбранных unit.bp и найденных связанных projectile.bp сохранены на листе «Все поля», включая визуальные и технические параметры. Унаследованные значения движка не подставлялись.'],
 ['Общее','Скрипты','Изменения во время игры, дочерние юниты и переключаемые режимы отражены в исходных скриптах и замечаниях. Числа в сравнении не являются результатом запуска симуляции.'],
 ['Общее','Проверка','Чертежи и связи снарядов прочитаны из локальных файлов. Все прямые и найденные дочерние ссылки на projectile.bp разрешены. Игра не запускалась.'],
 ['BlackOpsFAF','StellarBuff','Цена Philadelphia не меняется. При активном баффе ProductionPerSecondMass умножается на 2, ProductionPerSecondEnergy = исходное × 2 − 1. Основные таблицы показывают базовые значения.'],
 ...units.filter(u=>special[u.id]).map(u=>[u.id,u.name,special[u.id]])
];
const ns=table('Примечания','Определения, особенности и источники','Для поиска используйте ID юнита. Коды S001 и далее связывают данные с конкретным исходным файлом.',
 ['ID / раздел','Юнит / тема','Пояснение'],notes,{0:20,1:36,2:130},0);
ns.getRange(`C6:C${notes.length+5}`).format.wrapText=true;
ns.getRange(`A6:C${notes.length+5}`).format.rowHeight=48;
const sourceStart=notes.length+9;
ns.getRange(`A${sourceStart}`).values=[['Реестр источников']];
ns.getRange(`A${sourceStart}`).format.font={name:'Arial',size:14,bold:true,color:'#203853'};
const sourceRows=sources.map(p=>[sourceMap.get(p),p.includes('!/')?'Архив FAF / игры':'Локальный файл',p]);
ns.getRange(`A${sourceStart+2}:C${sourceStart+2+sourceRows.length}`).values=[['Код','Тип','Источник'],...sourceRows];
ns.tables.add(`A${sourceStart+2}:C${sourceStart+2+sourceRows.length}`,true,'SourcesTable').showFilterButton=true;
ns.getRange(`A${sourceStart+2}:C${sourceStart+2}`).format={fill:'#243F5B',font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},rowHeight:28};
ns.getRange(`A${sourceStart+3}:C${sourceStart+2+sourceRows.length}`).format.font={name:'Arial',size:10,color:'#202936'};
ns.getRange(`C${sourceStart+3}:C${sourceStart+2+sourceRows.length}`).format.wrapText=true;
ns.getRange(`A${sourceStart+3}:C${sourceStart+2+sourceRows.length}`).format.rowHeight=48;
ns.tabColor='#7C8795';

// Verify typed values and unit coverage before final export.
if(units.length!==24||units.filter(u=>!u.helper).length!==21||weaponRows.length!==136||data.missing.length)throw Error('Coverage mismatch');
if(sumRows.find(r=>r[0]==='GGA0403')[6]!==32000)throw Error('GGA0403 cost mismatch');
wb.recalculate();
const inspect=await wb.inspect({kind:'table',range:'Сравнение!A5:O10',include:'values,formulas',tableMaxRows:6,tableMaxCols:15,maxChars:4000});
console.log(inspect.ndjson);
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:20},summary:'Formula errors',maxChars:1500});
console.log(errors.ndjson);
for(const [name,s] of Object.entries(sheets)){
  const range=name==='Примечания'?'A2:C11':name==='Все поля'?'A2:H13':name==='Скрипты'?'A2:F13':name==='Оружие'?'A2:O13':name==='Сравнение'?'A2:O13':'A2:L13';
  const preview=await wb.render({sheetName:name,range,scale:1.25,format:'png'});
  await fs.writeFile(`${dir}/work/preview_${Object.keys(sheets).indexOf(name)+1}.png`,new Uint8Array(await preview.arrayBuffer()));
  console.log(`Rendered ${name}`);
}
const output=await SpreadsheetFile.exportXlsx(wb);
const filename=`${dir}/Экспериментальные_юниты_Seraphim_Rework_и_BlackOpsFAF.xlsx`;
await output.save(filename);
await fs.writeFile(`${dir}/work/verification.json`,JSON.stringify({units:units.length,main:21,helpers:3,weapons:weaponRows.length,fields:rawRows.length,scripts:scriptRows.length,sources:sources.length,sheets:Object.keys(sheets),output:filename},null,2));
console.log(JSON.stringify({output:filename,sheets:Object.keys(sheets).length,units:units.length,weapons:weaponRows.length,fields:rawRows.length}));
