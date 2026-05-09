#!/usr/bin/env python3
"""v19: rebuild the board routes/zones into a DRC-clean fabrication state.

The v18 broad GND via grid proved the remaining ratsnest items were just
unfilled-zone artifacts, but some of the vias landed on signal/power copper.
This revision removes the blind grid, moves a few colliding footprints, routes
around connector strain-relief holes, and fills zones with KiCad's PCB API.
"""
import uuid as _uuid, re
PCB="flipping-cool.kicad_pcb"
def uid(): return str(_uuid.uuid4())
def S(x1,y1,x2,y2,w,ly,n):
    return f'\t(segment\n\t\t(start {x1:.4f} {y1:.4f})\n\t\t(end {x2:.4f} {y2:.4f})\n\t\t(width {w})\n\t\t(layer "{ly}")\n\t\t(net {n})\n\t\t(uuid "{uid()}")\n\t)'
def V(x,y,n,sz=0.6,dr=0.3):
    return f'\t(via\n\t\t(at {x:.4f} {y:.4f})\n\t\t(size {sz})\n\t\t(drill {dr})\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net {n})\n\t\t(uuid "{uid()}")\n\t)'

def build():
    t=[];F="F.Cu";B="B.Cu"
    # ============ VBAT_RAW(14) ============
    t+=[V(18,4,14),S(16,8,18,4,0.8,F,14),S(18,4,34,4,0.8,B,14),V(34,4,14),S(34,4,36,8,0.8,F,14)]
    t+=[S(34,4,34,18,0.5,B,14),S(34,18,42,18,0.5,B,14),V(42,18,14),S(42,18,44,20,0.4,F,14)]
    t+=[S(34,18,26,18,0.5,B,14),S(26,18,26,25,0.5,B,14),V(26,25,14),S(26,25,28,25,0.4,F,14)]

    # ============ VBAT_SW(15) ============
    t+=[S(41,8,41,16,0.8,F,15),S(41,16,52,16,0.8,F,15),S(52,16,58,8,0.8,F,15)]
    t+=[S(52,16,107,16,0.8,F,15),S(107,16,110,8,0.8,F,15)]
    t+=[S(66,16,66,20,0.4,F,15)] # TP2
    t+=[S(41,16,39,30,0.5,F,15),S(39,30,40,30,0.5,F,15)] # J11.1
    t+=[V(37,32,15),S(39,30,37,32,0.3,F,15),S(37,32,20.91,32,0.3,B,15)]
    t+=[S(20.91,32,20.91,34,0.3,B,15),V(20.91,34,15),S(20.91,34,20.91,36,0.3,F,15)]
    t+=[V(44,32,15),S(39,30,44,32,0.4,F,15),S(44,32,49,32,0.4,B,15)]
    t+=[S(49,32,49,28,0.4,B,15),V(49,30,15),S(49,30,49,28,0.4,F,15)]
    t+=[S(49,32,56.95,32,0.3,B,15),V(56.95,32,15),S(56.95,32,56.95,30,0.3,F,15)]
    t+=[S(56.95,32,65,32,0.3,B,15),S(65,32,65,30,0.3,B,15),V(65,30,15),S(65,30,65,28,0.3,F,15)]

    # ============ SERVO_6V(13) ============
    t+=[S(119.6,8,119.6,12,0.6,F,13),S(119.6,12,138,12,0.6,F,13),S(138,12,138,38,0.6,F,13),S(138,38,129,38,0.6,F,13)]
    t+=[S(108.95,38,129,38,0.6,F,13)]
    t+=[S(110.95,38,110.95,44,0.4,F,13)] # C4.2
    t+=[S(108.95,38,102,38,0.4,F,13),S(102,38,102,40,0.4,F,13)] # C3.1
    t+=[S(102,38,84.5,38,0.4,F,13),S(84.5,38,84.5,58,0.4,F,13),S(84.5,58,83.46,58,0.4,F,13)] 
    t+=[S(129,38,129,90,0.6,F,13),S(13.46,90,129,90,0.6,F,13)]
    t+=[S(22,90,22,84,0.4,F,13)] # C7.1
    t+=[S(36,90,36,84,0.4,F,13)] # TP3
    t+=[S(13.46,90,13.46,96,0.4,F,13)] # J30.2
    t+=[S(27.46,90,27.46,96,0.4,F,13)] # J31.2
    # C8.2 to C7.1, doglegged around the adjacent GND pads.
    t+=[S(30.95,84,30.95,82,0.3,F,13),S(30.95,82,22,82,0.3,F,13),S(22,82,22,84,0.3,F,13)]

    # ============ RX_6V(12) ============
    t+=[S(80.54,58,80.54,60,0.3,F,12),S(80.54,60,88,60,0.3,F,12),S(88,60,88,58,0.3,F,12)] # C5.1
    t+=[S(88,58,88,56,0.3,F,12),S(88,56,96.95,56,0.3,F,12),S(96.95,56,96.95,58,0.3,F,12)] # C6.2
    t+=[S(96.95,58,98,58,0.3,F,12),V(98,58,12),S(98,58,98,68,0.3,B,12)]
    t+=[S(96.95,56,100,56,0.3,F,12)] # TP4 moved clear of J22 relief holes and PWM routes

    # ============ PWR_LED_A (1) ============
    # J3.1(15.00,30.00) to R1.1(19.0875,36.00)
    t+=[S(15,30,19.0875,30,0.25,F,1),S(19.0875,30,19.0875,36,0.25,F,1)]

    # ============ MOTORS ============
    t+=[S(82,8,78,8,0.6,B,17),S(78,8,78,97,0.6,B,17)]
    t+=[S(78,97,108,97,0.6,B,17),S(108,97,108,94,0.6,B,17)]
    t+=[S(108,97,122,97,0.6,B,17),S(122,97,122,94,0.6,B,17)]
    
    t+=[S(89,8,85,8,0.6,B,18),S(85,8,85,91,0.6,B,18)]
    t+=[S(85,91,105.5,91,0.6,B,18),S(105.5,91,105.5,94,0.6,B,18)]
    t+=[S(105.5,91,119.5,91,0.6,B,18),S(119.5,91,119.5,94,0.6,B,18)]
    
    t+=[S(96,8,92,8,0.6,B,19),S(92,8,92,83,0.6,B,19)]
    t+=[S(92,83,108,83,0.6,B,19),S(108,83,108,80,0.6,B,19)]
    t+=[S(108,83,122,83,0.6,B,19),S(122,83,122,80,0.6,B,19)]
    
    t+=[S(103,8,100,8,0.6,B,20),S(100,8,100,64,0.6,B,20)]
    t+=[S(100,64,118,64,0.6,B,20),S(118,64,118,77,0.6,B,20)]
    t+=[S(118,77,105.5,77,0.6,B,20),S(105.5,77,105.5,80,0.6,B,20)]
    t+=[S(118,77,119.5,77,0.6,B,20),S(119.5,77,119.5,80,0.6,B,20)]

    # ============ PWM signals ============
    t+=[S(74,47.08,72,47.08,0.25,F,6),S(72,47.08,72,64,0.25,F,6)]
    t+=[S(72,64,103.08,64,0.25,F,6),S(103.08,64,103.08,68,0.25,F,6)]

    t+=[S(74,49.62,76,49.62,0.25,F,7),S(76,49.62,76,62,0.25,F,7)]
    t+=[S(76,62,105.62,62,0.25,F,7),S(105.62,62,105.62,68,0.25,F,7)]

    t+=[S(108.16,68,108.16,70,0.25,F,10)]
    t+=[S(108.16,70,10,70,0.25,F,10)] 
    t+=[V(10,70,10),S(10,70,10,96,0.25,B,10)]
    t+=[S(10,96,10.92,96,0.25,B,10)]

    t+=[S(110.70,68,110.70,72,0.25,F,11)]
    t+=[S(110.70,72,20,72,0.25,F,11)] 
    t+=[V(20,72,11),S(20,72,20,100,0.25,B,11)]
    t+=[S(20,100,24.92,100,0.25,B,11),S(24.92,100,24.92,96,0.25,B,11)]
    return t

def build_zones():
    bp="(xy 10.8 0.8) (xy 129.2 0.8) (xy 139.2 10.8) (xy 139.2 99.2) (xy 129.2 109.2) (xy 10.8 109.2) (xy 0.8 99.2) (xy 0.8 10.8)"
    z=[]
    for ly in ["F.Cu","B.Cu"]:
        z.append(f'\t(zone\n\t\t(net 5)\n\t\t(net_name "GND_PWR")\n\t\t(layer "{ly}")\n\t\t(uuid "{uid()}")\n\t\t(hatch edge 0.5)\n\t\t(connect_pads yes\n\t\t\t(clearance 0.25)\n\t\t)\n\t\t(min_thickness 0.25)\n\t\t(filled_areas_thickness no)\n\t\t(fill yes\n\t\t\t(thermal_gap 0.5)\n\t\t\t(thermal_bridge_width 0.5)\n\t\t)\n\t\t(polygon\n\t\t\t(pts\n\t\t\t\t{bp}\n\t\t\t)\n\t\t)\n\t)')
    return z

def strip(c):
    c=re.sub(r'\t\(segment\n(?:\t\t[^\n]+\n)+\t\)\n','',c)
    c=re.sub(r'\t\(via\n(?:\t\t[^\n]+\n)+\t\)\n','',c)
    ls=c.split('\n');o=[];iz=False;d=0
    for l in ls:
        if not iz:
            if l.strip().startswith('(zone'):
                iz=True;d=sum(1 for c in l if c=='(')-sum(1 for c in l if c==')')
                if d<=0:iz=False
                continue
            o.append(l)
        else:
            d+=sum(1 for c in l if c=='(')-sum(1 for c in l if c==')')
            if d<=0:iz=False
    return '\n'.join(o)

def _footprint_span(c, ref):
    marker=f'(property "Reference" "{ref}"'
    mid=c.find(marker)
    if mid < 0:
        raise ValueError(f"missing footprint reference {ref}")
    start=c.rfind('\n\t(footprint ',0,mid)
    if start < 0:
        raise ValueError(f"cannot find footprint start for {ref}")
    start += 1
    d=0
    for i in range(start,len(c)):
        if c[i]=='(':
            d+=1
        elif c[i]==')':
            d-=1
            if d==0:
                return start,i+1
    raise ValueError(f"cannot find footprint end for {ref}")

def set_fp_at(c, ref, at):
    s,e=_footprint_span(c,ref)
    block=c[s:e]
    block=re.sub(r'\n\t\t\(at [^\n]+\)', f'\n\t\t(at {at})', block, count=1)
    return c[:s]+block+c[e:]

def set_fp_name(c, ref, libfp):
    s,e=_footprint_span(c,ref)
    block=c[s:e]
    block=re.sub(r'\(footprint "[^"]+"', f'(footprint "{libfp}"', block, count=1)
    return c[:s]+block+c[e:]

def move_fp_layer(c, ref, src, dst):
    s,e=_footprint_span(c,ref)
    block=c[s:e].replace(f'(layer "{src}")', f'(layer "{dst}")')
    return c[:s]+block+c[e:]

def normalize_footprints(c):
    # Keep the PCB in parity with schematic footprint library names.
    fpids={
        "J1":"Connector_AMASS:AMASS_XT30UPB-M_1x02_P5.0mm_Vertical",
        "J2":"Connector_AMASS:AMASS_XT30UPB-F_1x02_P5.0mm_Vertical",
        "J3":"Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical",
        "R1":"Resistor_SMD:R_0805_2012Metric",
        "J4":"Connector_JST:JST_XH_B3B-XH-A_1x03_P2.50mm_Vertical",
        "C1":"Capacitor_THT:CP_Radial_D6.3mm_P2.50mm",
        "C2":"Capacitor_SMD:C_0805_2012Metric",
        "D1":"Diode_SMD:D_SMA",
        "J5":"Connector_Wire:SolderWire-0.75sqmm_1x06_P4.8mm_D1.25mm_OD2.3mm_Relief2x",
        "FB1":"Resistor_SMD:R_1206_3216Metric",
        "C3":"Capacitor_THT:CP_Radial_D8.0mm_P3.50mm",
        "C4":"Capacitor_SMD:C_0805_2012Metric",
        "C5":"Capacitor_THT:CP_Radial_D6.3mm_P2.50mm",
        "C6":"Capacitor_SMD:C_0805_2012Metric",
        "J10":"Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical",
        "J11":"Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
        "J20":"Connector_AMASS:AMASS_XT30UPB-F_1x02_P5.0mm_Vertical",
        "J21":"Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
        "J22":"Connector_Wire:SolderWire-0.75sqmm_1x04_P7mm_D1.25mm_OD3.5mm_Relief2x",
        "J23":"Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical",
        "J24":"Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical",
        "J25":"Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical",
        "J26":"Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical",
        "J30":"Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
        "J31":"Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
        "C7":"Capacitor_THT:CP_Radial_D8.0mm_P3.50mm",
        "C8":"Capacitor_SMD:C_0805_2012Metric",
        "TP1":"TestPoint:TestPoint_Pad_D1.5mm",
        "TP2":"TestPoint:TestPoint_Pad_D1.5mm",
        "TP3":"TestPoint:TestPoint_Pad_D1.5mm",
        "TP4":"TestPoint:TestPoint_Pad_D1.5mm",
        "TP5":"TestPoint:TestPoint_Pad_D1.5mm",
    }
    for ref,libfp in fpids.items():
        c=set_fp_name(c,ref,libfp)
    # Move only the footprints involved in real DRC collisions.
    for ref,at in {
        "J5":"110 8",
        "MH2":"132 48",
        "C4":"110 44",
        "C6":"96 58",
        "TP4":"100 56",
    }.items():
        c=set_fp_at(c,ref,at)
    # Keep J22 matching the KiCad library footprint if this script is rerun
    # after an earlier local silkscreen experiment.
    c=move_fp_layer(c,"J22","Dwgs.User","B.SilkS")
    return c

def fill_zones():
    try:
        import pcbnew
    except Exception as e:
        print(f"Warning: pcbnew unavailable, zones left unfilled: {e}")
        return
    b=pcbnew.LoadBoard(PCB)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(PCB,b)

def main():
    with open(PCB,'r') as f:c=f.read()
    c=normalize_footprints(c)
    c=strip(c);t=build();z=build_zones()
    p=c.rstrip().rfind(')');n=c[:p]+'\n'
    for x in t:n+=x+'\n'
    for x in z:n+=x+'\n'
    n+=c[p:]
    with open(PCB,'w') as f:f.write(n)
    fill_zones()
    print(f"Done: {len(t)} elements, {len(z)} zones")

if __name__=='__main__':main()
