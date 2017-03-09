// -*- coding: utf-8 -*-
// Copyright (c) 2015, Kevin Läufer
// Copyright (c) 2016, Niklas Hauser
// All rights reserved.
//
// The file is part of the modm project
//
// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at http://mozilla.org/MPL/2.0/.

package izpack_deserializer;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.ObjectInputStream;
import java.io.OptionalDataException;
import java.io.OutputStream;
import java.io.FileOutputStream;

import com.izforge.izpack.api.data.PackFile;

public class IzPackDeserializer {
	public static void unpackFile(InputStream in, File target, long length) {
		try {
			OutputStream out = new FileOutputStream(target);
			byte[] buffer = new byte[5120];
			long bytesCopied = 0;
			while(bytesCopied < length) {
				int maxBytes = (int) Math.min(length - bytesCopied, buffer.length);
				int read = in.read(buffer, 0, maxBytes);
				if(read == -1) {
					throw new IOException("Unexpected end of stream (installer corrupted?)");
				}
				out.write(buffer, 0, read);
				bytesCopied += read;
			}
			out.close();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}

	public static void main(String[] args) {
		System.out.println("IzPackDeserializer");
		final String input = "../temp/resources/packs/pack-Core";
		final String output = "../output";
		PackFile pf = null;
		FileInputStream inputFileStream;

		try {
			inputFileStream = new FileInputStream(input);
			ObjectInputStream stream = new ObjectInputStream(inputFileStream);

			int fileCount = stream.readInt();
			System.out.println(fileCount);

			for(int ii = 0; ii < fileCount; ++ii) {
				pf = (PackFile)stream.readObject();
				System.out.println(pf.targetPath);
				if(pf.targetPath.startsWith("$INSTALL_PATH/db/")) {
					System.out.println(pf.length);
					System.out.println(pf.targetPath);
					System.out.println(pf.previousPackId);
					String target_name = pf.targetPath.replace("$INSTALL_PATH", output);
					File target = new File(target_name);
					if(pf.isDirectory) {
						target.mkdirs();
					}
					if(!pf.isDirectory && pf.length > 0) {
						unpackFile(stream, target, pf.length);
					}
					stream.skip(pf.length);
				} else {
					stream.skip(pf.length);
				}
			}
			stream.close();
			inputFileStream.close();
		} catch (OptionalDataException e){
			e.printStackTrace();
		} catch (ClassNotFoundException e){
			e.printStackTrace();
		} catch (IOException e) {
			e.printStackTrace();
		}
	}
}
