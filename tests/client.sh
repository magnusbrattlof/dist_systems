for ip in `seq 1 8`; do
	for i in `seq 1 5`; do
		curl -d 'entry=t'${i} -X 'POST' 'http://10.1.0.'${ip}'/board' &
	done
done