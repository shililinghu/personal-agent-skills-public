"""Opt-in source-PNG triage for named Cocos2 standalone SpriteFrames.
Signals need human comparison; not an art verdict or a full bundle-format verifier.
"""
import argparse,base64,hashlib,json,re
from collections import deque
from pathlib import Path

def decode(value):
    if not isinstance(value,str):raise ValueError('texture UUID must be a string')
    if len(value)==22:
        raw=value[:2]+base64.b64decode(value[2:]+'==',validate=True).hex()
        value='-'.join([raw[:8],raw[8:12],raw[12:16],raw[16:20],raw[20:]])
    if not re.fullmatch(r'[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}',value):raise ValueError('unsupported texture UUID')
    return value

def runlen(values):
    best=length=0
    for item in values:length=length+1 if item else 0;best=max(best,length)
    return best

def inspect_texture(path):
    from PIL import Image
    with Image.open(path) as source:im=source.convert('RGBA')
    width,height=im.size;mask=bytearray(v>64 for v in im.getchannel('A').tobytes())
    if not any(mask):return {'size':[width,height],'suspects':['empty_alpha'],'edge_runs':{},'components':[]}
    edges={'top':mask[:width],'bottom':mask[-width:],'left':mask[::width],'right':mask[width-1::width]}
    cuts={key:runlen(values) for key,values in edges.items() if runlen(values)>=max(16,len(values)*.15)}
    remaining=mask[:];areas=[]
    for i in range(width*height):
        if not remaining[i]:continue
        queue=deque([i]);remaining[i]=0;area=0
        while queue:
            z=queue.popleft();area+=1;x=z%width;y=z//width
            for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if 0<=xx<width and 0<=yy<height:
                    index=yy*width+xx
                    if remaining[index]:remaining[index]=0;queue.append(index)
        areas.append(area)
    areas.sort(reverse=True);fragments=[n for n in areas[1:] if n>=max(80,areas[0]*.025)]
    signals=(['straight_source_edge'] if cuts else [])+(['extra_alpha_components'] if fragments else [])
    return {'size':[width,height],'suspects':signals,'edge_runs':cuts,'components':fragments}

def check(root,names,role='single_body'):
    root=Path(root).resolve();names=list(dict.fromkeys(names));errors=[];matches={name:[] for name in names}
    if not root.is_dir() or not names or any(not isinstance(n,str) or not n for n in names):
        return {'input':str(root),'status':'incomplete','passed':False,'checked':0,'missing':names,'errors':['Native root and explicit frame names required'],'rows':[],'art_verdict':'not_assessed'}
    if role not in ('single_body','background','tile','multi_body'):raise ValueError('unsupported role')
    if role!='single_body':
        return {'input':str(root),'status':'not_applicable','passed':None,'checked':0,'missing':[],'errors':[],'rows':[],'role':role,'art_verdict':'not_assessed'}
    # Limited profile: standalone import/*.json + sibling native directory.
    # Scan both main assets and ordinary subpackages; unknown layouts remain incomplete.
    folders=sorted(set(root.glob('assets/*/import'))|set(root.glob('subpackages/*/import')))
    for folder in folders:
        for p in folder.rglob('*.json'):
            try:
                doc=json.loads(p.read_text())
                if not isinstance(doc,list) or len(doc)<6 or not isinstance(doc[5],list) or not doc[5] or not isinstance(doc[5][0],dict):continue
                name=doc[5][0].get('name')
                if name not in matches:continue
                uuid=decode(doc[1][0]);native=folder.parent/'native'
                textures=list(native.rglob(uuid+'.png'))
                if len(textures)!=1:raise ValueError('missing/ambiguous standalone PNG')
                path=textures[0].resolve()
                if not path.is_relative_to(root):raise ValueError('texture outside Native root')
                matches[name].append(path)
            except (OSError,ValueError,TypeError,IndexError,KeyError) as exc:
                errors.append({'path':str(p.relative_to(root)),'error':str(exc)})
    rows=[];cache={}
    for name,paths in matches.items():
        if len(paths)!=1:
            if len(paths)>1:errors.append({'frame':name,'error':'ambiguous frame name across bundles'})
            continue
        path=paths[0]
        try:
            if path not in cache:cache[path]=dict(inspect_texture(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            row=dict(cache[path],name=name,texture=str(path.relative_to(root)));rows.append(row)
        except (OSError,ValueError,ImportError) as exc:errors.append({'frame':name,'error':str(exc)})
    missing=sorted(set(names)-{row['name'] for row in rows});review=any(row['suspects'] for row in rows)
    status='incomplete' if missing or errors or not rows else 'needs_review' if review else 'no_signals'
    return {'input':str(root),'status':status,'passed':status=='no_signals','checked':len(rows),'missing':missing,'errors':errors,'rows':rows,'art_verdict':'not_assessed','coverage':'named standalone Cocos2 SpriteFrame/PNG source signals only; actual frame rect and whole-page composition need project observation'}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('native_root',type=Path);parser.add_argument('frames',nargs='+');parser.add_argument('--role',choices=['single_body','background','tile','multi_body'],default='single_body');args=parser.parse_args()
    result=check(args.native_root,args.frames,args.role);print(json.dumps(result,ensure_ascii=False,indent=2))
    return 2 if result['status']=='incomplete' else 1 if result['status']=='needs_review' else 0
if __name__=='__main__':raise SystemExit(main())
