<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
</head>
<body>
<div style="font-family: monospace; font-size: 14px">
<?php
	$dir = opendir('.');
	while (true == ($logfiles []= readdir($dir))); // end of loop
	closedir($dir);
	sort($logfiles);
	$logfiles = array_reverse($logfiles);
	$backgrounds = array(
		0 => '#ffffff',
		1 => '#ffdddd',
	);
	foreach ($logfiles as $key=>$l) {
		if (substr(strrchr($l,'.'), 1) == 'log') {
			echo '<div style="margin:3px;background:' .$backgrounds[$key%2]. ';';
			echo '"><a href="viewlog.php?l=' . $l . '">' . $l . '</a> ' . count(file($l)). ' lines</div>'."\n";
		}
	}
	// VAR_DUMP($logfiles);
?>
</div>
</body>
</html>
