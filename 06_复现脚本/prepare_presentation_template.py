"""Duplicate the supplied content slide while preserving its theme, logo and layout.
Usage: python prepare_presentation_template.py TEMPLATE_PPTX OUTPUT_PPTX [COUNT]
This performs file/structure conversion only; all scientific figures are drawn in R.
"""
from copy import deepcopy
from pathlib import Path
import sys
from pptx import Presentation

def main():
    source,target=map(Path,sys.argv[1:3]);count=int(sys.argv[3]) if len(sys.argv)>3 else 18
    p=Presentation(source)
    if len(p.slides)!=1:
        raise ValueError('This course layout expects a one-slide template')
    original=p.slides[0]
    for _ in range(count-1):
        s=p.slides.add_slide(original.slide_layout)
        for sh in list(s.shapes):
            s.shapes._spTree.remove(sh._element)
        relation_map={}
        for r in original.part.rels.values():
            if r.reltype.endswith(('/slideLayout','/notesSlide')):
                continue
            relation_map[r.rId]=s.part.rels.get_or_add_ext_rel(r.reltype,r.target_ref) if r.is_external else s.part.rels.get_or_add(r.reltype,r.target_part)
        for sh in original.shapes:
            el=deepcopy(sh._element)
            for n in el.iter():
                for k,v in list(n.attrib.items()):
                    if k.startswith('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}') and v in relation_map:
                        n.set(k,relation_map[v])
            s.shapes._spTree.insert_element_before(el,'p:extLst')
    target.parent.mkdir(parents=True,exist_ok=True)
    p.save(target)
    print(f'Prepared {len(p.slides)} template slides')

if __name__=='__main__':main()
