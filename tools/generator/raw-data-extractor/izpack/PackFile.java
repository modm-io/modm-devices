/*
 * IzPack - Copyright 2001-2008 Julien Ponge, All Rights Reserved.
 *
 * http://izpack.org/
 * http://izpack.codehaus.org/
 *
 * Copyright 2001 Johannes Lehtinen
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.izforge.izpack.api.data;

import java.io.Serializable;
import java.util.List;
import java.util.Map;

/**
 * Encloses information about a packed file. This class abstracts the way file data is stored to
 * package.
 *
 * @author Johannes Lehtinen <johannes.lehtinen@iki.fi>
 */
public class PackFile implements Serializable
{

    static final long serialVersionUID = -834377078706854909L;

    /**
     * Only available when compiling. Makes no sense when installing, use relativePath instead.
     */
    public transient String sourcePath = null;//should not be used anymore - may deprecate it.
    /**
     * The Path of the file relative to the given (compiletime's) basedirectory.
     * Can be resolved while installing with either current working directory or directory of "installer.jar".
     */
    public String relativePath = null;

    /**
     * The full path name of the target file
     */
    public String targetPath = null;

    /**
     * The target operating system constraints of this file
     */
    public List<OsModel> osConstraints = null;

    /**
     * The length of the file in bytes
     */
    public long length = 0;

    /**
     * The size of the file used to calculate the pack size
     */
    public transient long size = 0;

    /**
     * The last-modification time of the file.
     */
    public long mtime = -1;

    /**
     * True if file is a directory (length should be 0 or ignored)
     */
    public boolean isDirectory = false;

    /**
     * Whether or not this file is going to override any existing ones
     */
    public OverrideType override;

    /**
     * Glob mapper expression for mapping the resulting file name if overriding is allowed and the
     * file does already exist. This is similar like the Ant globmapper target expression when
     * mapping from "*".
     */
    public String overrideRenameTo;

    /**
     * Whether or not this file might be blocked by the operating system
     */
    public Blockable blockable = Blockable.BLOCKABLE_NONE;

    /**
     * Additional attributes or any else for customisation
     */
    public Map additionals = null;

    public String previousPackId = null;

    public long offsetInPreviousPack = -1;

    /**
     * True if the file is a Jar and pack200 compression us activated.
     */
    public boolean pack200Jar = false;

    /**
     * condition for this packfile
     */
    public String condition = null;
}
