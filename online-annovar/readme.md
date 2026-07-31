perl /home/TOOLS/tools/annovar/current/bin/table_annovar.pl input.vcf /humandb/ -buildver hg38 -out P260416017.var -remove \
	-protocol refGeneWithVer \
	-operation g \
	-nastring . \
	-vcfinput \
	--polish \
	--argument '-hgvs -splicing_threshold 10'

perl /home/TOOLS/tools/annovar/current/bin/annotate_variation.pl --downdb refGeneWithVer /humandb

perl /home/TOOLS/tools/annovar/current/bin/convert2annovar.pl -format vcf4 input.vcf > input.avinput

awk 'BEGIN{OFS="\t"} /^##/{print; next} /^#CHROM/{print $1,$2,$3,$4,$5,$6,$7,$8; next} {print $1,$2,$3,$4,$5,$6,$7,$8}' P260413007_FLT3_ITD.vcf > P260413007_FLT3_ITD.annovar.vcf

perl /home/TOOLS/tools/annovar/current/bin/convert2annovar.pl -format vcf4 P260413007_FLT3_ITD.annovar.vcf > P260413007_FLT3_ITD.avinput