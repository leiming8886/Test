#-------------------------------------------------------------------------------
# Name:        ??1
# Purpose:
#
# Author:      user
#
# Created:     29/01/2014
# Copyright:   (c) user 2014
# Licence:     <your licence>
#-------------------------------------------------------------------------------

from optparse import OptionParser
from Gtf import Gtf
from Table import Table
from sets import Set
import subprocess
import shlex
import os
import time


def sub_array(A,B):
    x=Set(A)
    y=Set(B)
    return list(x - y)

def intersect_array(A,B):
    x=Set(A)
    y=Set(B)
    return list(x & y)


def union_array(A,B):
    x=Set(A)
    y=Set(B)
    return list(x | y)

def de_redundency(A):
    return list(Set(A))

def fetch_args():
    usage="""

        compare.py: compare the merged/assembled transcripts with known gene annotation!
        Usage: compare.py [-h] -c coding_ref -n noncoding_ref -i input_gtf -o out_dir

    """
    parser = OptionParser(usage=usage)
    parser.add_option("-c", "--coding_ref", dest="coding_ref", help="(Required.) "
                      +"The path of coding reference gtf file. Two mandatory attributes"
                      +" (gene_id \"value\"; transcript_id \"value\") should be provided in the file. "
                      +"Some files which has already been prepared could be download at"
                      +" http://wwww.bioinfo.org/software/cnci .")
    parser.add_option("-n", "--noncoding_ref", dest="noncoding_ref", help="(Required.) "
                      +"The path of lincRNA reference gtf file. Two mandatory attributes"
                      +" (gene_id \"value\"; transcript_id \"value\") should be provided in the file. "
                      +"Some files which has already been prepared could be download at"
                      +" http://wwww.bioinfo.org/software/cnci .")
    parser.add_option("-i", "--input_gtf", dest="input_gtf", help="(Required.) "
                      +"The path of user input assemble gtf file. Two mandatory attributes"
                      +" (gene_id \"value\"; transcript_id \"value\") should be provided in the file. "
                      +"This file usually be generated by cufflinks/cuffcompare/cuffmerge.")
    parser.add_option("-o", "--out_dir", dest="out_dir", help="(Required.) Output dirctory of the results.")
    (options, args) = parser.parse_args()
    if options.coding_ref is not None:
        coding_ref=options.coding_ref
    else:
        print parser.print_help()
        exit("Error: Coding reference file is required!")
    if options.noncoding_ref is not None:
        noncoding_ref=options.noncoding_ref
    else:
        print parser.print_help()
        exit("Error: Noncoding reference file is required!")
    if options.input_gtf is not None:
        input_gtf=options.input_gtf
    else:
        print parser.print_help()
        exit("Error: User input assembly file is required!")
    if options.out_dir is not None:
        out_dir=options.out_dir
        out_dir=out_dir.rstrip('/')
    else:
        print parser.print_help()
        exit("Error: Output directory is required!")
    return (coding_ref,noncoding_ref,out_dir,input_gtf)

def make_dir(filepath):
    if not os.path.exists(filepath):
        os.makedirs(filepath)

def prepare_dirs(out_dir):
    if out_dir:
        make_dir(out_dir)
        cuffcompare_outdir=out_dir+ '/cuffcompare'
        gtf_outdir=out_dir+'/gtf'
    else:
        cuffcompare_outdir='cuffcompare'
        gtf_outdir='gtf'
        out_dir="."
    make_dir(cuffcompare_outdir)
    #make_dir(gtf_outdir)
    return (cuffcompare_outdir,gtf_outdir)

def erase_strand(input_gtf,new_file):
    result=Table(input_gtf,0,False)
    result.update_col(7,'+')
    result.write_to_file(new_file)

def fetch_gtfs(coding_ref_input,noncoding_ref_input,combined_gtf_input,cuffcompare_outdir):
    coding_ref=cuffcompare_outdir+"/coding.gtf"
    noncoding_ref=cuffcompare_outdir+"/noncoding.gtf"
    combined_gtf=cuffcompare_outdir+"/combined.gtf"
    erase_strand(coding_ref_input,coding_ref)
    erase_strand(noncoding_ref_input,noncoding_ref)
    erase_strand(combined_gtf_input,combined_gtf)
    return (coding_ref,noncoding_ref,combined_gtf)

def cuffcompare(db,query,out_pre):
    query_dir=os.path.split(query)[0]
    query_dir=(query_dir=="" and "./") or query_dir
    query_filename=os.path.split(query)[1]
    out_pre_tag=os.path.split(out_pre)[1]
    cuffcompare_cmd='cuffcompare -r ' + db +' -o '+ out_pre + ' ' + query
    cuffcompare_cmd=shlex.split(cuffcompare_cmd)
    stdoutfile=out_pre + '.log'
    stderrfile=out_pre + '.err'
    cuffcompare_proc = subprocess.call(cuffcompare_cmd,stdout=open(stdoutfile,'w'),stderr=open(stderrfile,'w'))
    if cuffcompare_proc:
        print("Error: Cuffcompare break!, The command: "+" ".jon(cuffcompare_cmd))
        exit("See std_log: "+stdoutfile+", err_log: "+stderrfile+" for more detail")
    query_dir=query_dir.rstrip('/')
    tmap_file=query_dir+"/"+out_pre_tag+"."+query_filename+".tmap"
    return Table(tmap_file,0,True)

def classify(KC,overlap_KC,KN,overlap_KN,discard_cnc_tmap_gids,unannotated):
    result=Table()
    result.key=1
    result.col_names=['gid','class']
    for i in KC:
        result.data.append([i,'known_coding'])
        result.row_names[i]=len(result.row_names)
    for i in overlap_KC:
        result.data.append([i,'undefinable'])
        result.row_names[i]=len(result.row_names)
    for i in KN:
        result.data.append([i,'known_lincRNA'])
        result.row_names[i]=len(result.row_names)
    for i in overlap_KN:
        result.data.append([i,'undefinable'])
        result.row_names[i]=len(result.row_names)
#    for i in discard_cnc_tmap_gids:
#        result.data.append([i,'discarded'])
#        result.row_names[i]=len(result.row_names)
    for i in unannotated:
        result.data.append([i,'potentially_novel'])
        result.row_names[i]=len(result.row_names)
    return result

def related_gene(related_gene):
    gene_class=related_gene[1]
    coding=related_gene[2]
    noncoding=related_gene[3]
    overlap_coding=related_gene[4]
    overlap_noncoding=related_gene[5]
    if gene_class =="known_coding":
        return coding
    elif gene_class == "known_lincRNA":
        return noncoding
    elif gene_class == "undefinable":
        if overlap_coding!= "":
            return overlap_coding
        elif overlap_noncoding!="":
            return overlap_noncoding
        else:
            return "-"
    else:
        return "-"


(coding_ref_input,noncoding_ref_input,out_dir,combined_gtf_input)=fetch_args()
start_time=time.time()
print "Classification start:"
(cuffcompare_outdir,gtf_outdir)=prepare_dirs(out_dir)
(coding_ref,noncoding_ref,combined_gtf)=fetch_gtfs(
                                      coding_ref_input, noncoding_ref_input,
                                      combined_gtf_input, cuffcompare_outdir)
gtf=Gtf.simple_read(combined_gtf_input)
tid_gid=gtf.get_tid_gid()
gid_tid=tid_gid.key_by([2],[1])
all_gids=gid_tid.getCol(1)

print "Input genes: ", len(all_gids)

print "Running Cuffcompare ..."
strand_coding_tmap=cuffcompare(coding_ref_input,combined_gtf_input,cuffcompare_outdir+'/strandc')
strand_coding_tmap.update_col('cuff_gene_id',gtf.get_gid(strand_coding_tmap.getCol('cuff_id')))
strand_noncoding_tmap=cuffcompare(noncoding_ref_input,combined_gtf_input,cuffcompare_outdir+'/strandnc')
strand_noncoding_tmap.update_col('cuff_gene_id',gtf.get_gid(strand_noncoding_tmap.getCol('cuff_id')))


coding_tmap=cuffcompare(coding_ref,combined_gtf,cuffcompare_outdir+'/coding')
coding_tmap.update_col('cuff_gene_id',gtf.get_gid(coding_tmap.getCol('cuff_id')))
noncoding_tmap=cuffcompare(noncoding_ref,combined_gtf,cuffcompare_outdir+'/noncoding')
noncoding_tmap.update_col('cuff_gene_id',gtf.get_gid(noncoding_tmap.getCol('cuff_id')))

print "Classifying based on Cuffcompare results:"
known_coding=strand_coding_tmap.eget('union','_class_code==','_class_code=c','_class_code=j')
known_coding=known_coding.get_col(1,4).de_redundency().key_by([2],[1])


overlap_coding=coding_tmap.eget('union','_class_code=e','_class_code=o','_class_code=p',
                                 '_class_code=r','_class_code=x','_class_code=s','_class_code=.')
overlap_coding=overlap_coding.get_col(1,4).de_redundency().key_by([2],[1])


known_noncoding=strand_noncoding_tmap.eget('union','_class_code==','_class_code=c','_class_code=j')
known_noncoding=known_noncoding.get_col(1,4).de_redundency().key_by([2],[1])


overlap_noncoding=noncoding_tmap.eget('union','_class_code=e','_class_code=o','_class_code=p',
                                 '_class_code=r','_class_code=x','_class_code=s','_class_code=.')
overlap_noncoding=overlap_noncoding.get_col(1,4).de_redundency().key_by([2],[1])


coding_linc=coding_tmap.eget('union','_class_code=u','_class_code=i')
coding_linc=coding_linc.get_col(1,4).de_redundency().key_by([2],[1])

noncoding_linc=noncoding_tmap.eget('union','_class_code=u','_class_code=i')
noncoding_linc=noncoding_linc.get_col(1,4).de_redundency().key_by([2],[1])



coding_tmap_gids=de_redundency(coding_tmap.getCol('cuff_gene_id'))
noncoding_tmap_gids=de_redundency(noncoding_tmap.getCol('cuff_gene_id'))
discard_coding_tmap_gids=sub_array(all_gids,coding_tmap_gids)
discard_noncoding_tmap_gids=sub_array(all_gids,noncoding_tmap_gids)
discard_cnc_tmap_gids=intersect_array(discard_coding_tmap_gids,discard_noncoding_tmap_gids)

KC=known_coding.getCol(1)
print "Known coding genes:",len(KC)
not_KC=sub_array(all_gids,KC)
overlap_KC=intersect_array(not_KC,overlap_coding.getCol(1))
#print "overlap coding:",len(overlap_KC)
linc_KC=sub_array(not_KC,overlap_KC)
KN=intersect_array(known_noncoding.getCol(1),linc_KC)
print "Known lincRNA genes:",len(KN)
not_KN=sub_array(linc_KC,KN)
overlap_KN=intersect_array(not_KN,overlap_noncoding.getCol(1))
#print "overlap lincRNA:",len(overlap_KN)
#print "discarded:",len(discard_cnc_tmap_gids)
undefinable=union_array(overlap_KC,overlap_KN)
print "Undefinable genes:", len(undefinable)
unannotated=sub_array(not_KN,overlap_KN)
unannotated=sub_array(unannotated,discard_cnc_tmap_gids)
print "Potentially novel genes:",len(unannotated)
print "Genes missing classification by cuffcompare:", len(discard_cnc_tmap_gids)


print "Saving gtf files ..."
gene_class_outfile=out_dir+"/compare_1_infor.txt"
kc_gtf=out_dir+"/known_coding.gtf"
#overlap_kc_gtf=out_dir+"/overlap_coding.gtf"
kn_gtf=out_dir+"/known_lincRNA.gtf"
#overlap_kn_gtf=out_dir+"/overlap_lincRNA.gtf"
#discard_cnc_tmap_gids_gtf=out_dir+"/discarded.gtf"
undefinable_gtf=out_dir+"/undefinable.gtf"
unannotated_gtf=out_dir+"/potentially_novel.gtf"
#kc_go_outfile=out_dir+"/known_coding_gene_annotation"
#t2g_file=out_dir+"/tid_gid"
gene_class=classify(KC,overlap_KC,KN,overlap_KN,discard_cnc_tmap_gids,unannotated)
all_info=Table.paste(gene_class,[1],known_coding,[1],known_noncoding,[1],overlap_coding,[1],overlap_noncoding,[1])
all_info.col_names[2]='related_coding_gene'
all_info.col_names[3]='related_linc_gene'
all_info.col_names[4]='overlap_coding_gene'
all_info.col_names[5]='overlap_noncoding_gene'
all_info.append_col_by_func('related_ref_genes',related_gene)
all_info=all_info.get_col(1,2,'related_ref_genes')
all_info.set_colnames('input_gene_id','class','ref_gene_info')
#print "Class of genes is saved to '" +gene_class_outfile+"'"
all_info.write_to_file(gene_class_outfile)

#tid_gid.write_to_file(t2g_file)
#print "Generating known coding genes file:"
gtf.sub_gtf(gtf.get_tid(KC)).write_to_file(kc_gtf)
#print "Generating overlap coding genes file:"
#gtf.sub_gtf(gtf.get_tid(overlap_KC)).write_to_file(overlap_kc_gtf)
#print "Generating known lincRNA genes file:"
gtf.sub_gtf(gtf.get_tid(KN)).write_to_file(kn_gtf)
#print "Generating overlap lincRNA genes file:"
#gtf.sub_gtf(gtf.get_tid(overlap_KN)).write_to_file(overlap_kn_gtf)
#print "Generating discarded genes file:"
#gtf.sub_gtf(gtf.get_tid(discard_cnc_tmap_gids)).write_to_file(discard_cnc_tmap_gids_gtf)
#print "Generating undefinable genes file:"
gtf.sub_gtf(gtf.get_tid(undefinable)).write_to_file(undefinable_gtf)
#print "Generating potentially_novel genes file:"
gtf.sub_gtf(gtf.get_tid(unannotated)).write_to_file(unannotated_gtf)

##if gene_anno:
##    known_coding_disabond=known_coding.disabond_col(2,",")
##    kc_go=Table.fuzzy_paste(known_coding_disabond,[2],Table(gene_anno,0,False),[1])
##    kc_go=kc_go.eget('intersect','2!=','3!=')
##    kc_go=kc_go.get_col(2,3,1)
##    kc_go=kc_go.disabond_col(1,',')
##    kc_go=kc_go.disabond_col(2,',')
##    kc_go=kc_go.de_redundency(1,2)
##    kc_go.write_to_file(kc_go_outfile)
run_time=int((time.time() - start_time)/60)
exit("Classificaton complete: "+"%d minutes elapsed " % run_time)

